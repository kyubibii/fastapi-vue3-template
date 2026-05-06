<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>配置项管理</span>
          <div class="header-actions">
            <el-button
              v-if="permStore.hasPermission('system.settings.create')"
              type="primary"
              @click="openCreateDialog"
            >
              在当前分组新增
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeGroup" @tab-change="handleTabChange">
        <el-tab-pane
          v-for="group in groups"
          :key="group"
          :label="groupLabel(group)"
          :name="group"
        />
      </el-tabs>

      <el-form inline class="filter-form">
        <el-form-item label="配置名">
          <el-input
            v-model="filters.setting_name"
            placeholder="请输入配置名"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="settings" stripe>
        <el-table-column prop="setting_name" label="配置名" min-width="220" />
        <el-table-column
          prop="setting_value"
          label="配置值"
          min-width="220"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span>{{ row.setting_value ?? "—" }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="value_type" label="类型" width="100" />
        <el-table-column
          prop="description"
          label="说明"
          min-width="180"
          show-overflow-tooltip
        />
        <el-table-column label="属性" width="220">
          <template #default="{ row }">
            <el-tag v-if="row.is_sensitive" type="warning" size="small"
              >敏感</el-tag
            >
            <el-tag
              v-if="row.is_readonly"
              type="info"
              size="small"
              class="attr-tag"
              >只读</el-tag
            >
            <el-tag
              v-if="row.is_encrypted"
              type="success"
              size="small"
              class="attr-tag"
              >加密</el-tag
            >
          </template>
        </el-table-column>
        <el-table-column
          prop="updated_at"
          label="更新时间"
          width="180"
          :formatter="fmtDate"
        />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="permStore.hasPermission('system.settings.update')"
              size="small"
              :disabled="row.is_readonly"
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @change="fetchSettings"
      />
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="640px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="配置名" prop="setting_name">
          <el-input v-model="form.setting_name" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="配置分组" prop="setting_group">
          <el-select
            v-model="form.setting_group"
            filterable
            allow-create
            default-first-option
          >
            <el-option
              v-for="group in groups"
              :key="group"
              :label="groupLabel(group)"
              :value="group"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="值类型" prop="value_type">
          <el-select v-model="form.value_type">
            <el-option label="string" value="string" />
            <el-option label="int" value="int" />
            <el-option label="bool" value="bool" />
            <el-option label="json" value="json" />
          </el-select>
        </el-form-item>
        <el-form-item label="配置值" prop="setting_value">
          <el-input
            v-model="form.setting_value"
            type="textarea"
            :rows="form.value_type === 'json' ? 6 : 3"
            placeholder="敏感项支持覆盖写入，后端不会回显原值"
          />
        </el-form-item>
        <el-form-item label="说明" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="属性">
          <el-space>
            <el-checkbox v-model="form.is_sensitive">敏感</el-checkbox>
            <el-checkbox v-model="form.is_encrypted">加密</el-checkbox>
            <el-checkbox v-model="form.is_readonly">只读</el-checkbox>
          </el-space>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm"
          >保存</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { settingsApi, type SettingPublic } from "@/api/settings";
import { usePermissionStore } from "@/stores/permission";

type SettingValueType = "string" | "int" | "bool" | "json";

const permStore = usePermissionStore();

const loading = ref(false);
const saving = ref(false);
const settings = ref<SettingPublic[]>([]);
const groups = ref<string[]>([]);
const activeGroup = ref("");
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const filters = reactive({ setting_name: "" });

const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const formRef = ref<FormInstance>();

const form = reactive({
  setting_name: "",
  setting_group: "",
  setting_value: "",
  description: "",
  value_type: "string" as SettingValueType,
  is_sensitive: false,
  is_encrypted: false,
  is_readonly: false,
});

const isEdit = computed(() => editingId.value !== null);
const dialogTitle = computed(() =>
  isEdit.value ? "编辑配置项" : "新增配置项",
);

const rules: FormRules = {
  setting_name: [
    { required: true, message: "请输入配置名", trigger: "blur" },
    { min: 1, max: 100, message: "长度需在 1-100 之间", trigger: "blur" },
  ],
  setting_group: [
    { required: true, message: "请输入配置分组", trigger: "change" },
  ],
  value_type: [{ required: true, message: "请选择值类型", trigger: "change" }],
};

function groupLabel(group: string): string {
  const map: Record<string, string> = {
    display: "展示配置",
    feature: "功能开关",
    email: "邮件配置",
    security: "安全配置",
  };
  return map[group] ?? group;
}

function fmtDate(_row: unknown, _col: unknown, val: string | null) {
  return val ? new Date(val).toLocaleString("zh-CN") : "—";
}

function resetFormValues(): void {
  form.setting_name = "";
  form.setting_group = activeGroup.value || groups.value[0] || "";
  form.setting_value = "";
  form.description = "";
  form.value_type = "string";
  form.is_sensitive = false;
  form.is_encrypted = false;
  form.is_readonly = false;
}

async function fetchGroups(): Promise<void> {
  try {
    const res = await settingsApi.groups();
    groups.value = res.data.data.map((item) => item.setting_group);
    if (!groups.value.length) {
      groups.value = ["display", "feature", "email", "security"];
    }
    if (!activeGroup.value || !groups.value.includes(activeGroup.value)) {
      activeGroup.value = groups.value[0];
    }
  } catch {
    groups.value = ["display", "feature", "email", "security"];
    activeGroup.value = groups.value[0];
  }
}

async function fetchSettings(): Promise<void> {
  loading.value = true;
  try {
    const skip = (currentPage.value - 1) * pageSize.value;
    const res = await settingsApi.list({
      skip,
      limit: pageSize.value,
      setting_group: activeGroup.value || undefined,
      setting_name: filters.setting_name || undefined,
    });
    settings.value = res.data.data;
    total.value = res.data.count;
  } catch {
    ElMessage.error("加载配置项失败");
  } finally {
    loading.value = false;
  }
}

function handleTabChange(): void {
  currentPage.value = 1;
  fetchSettings();
}

function handleSearch(): void {
  currentPage.value = 1;
  fetchSettings();
}

function resetFilters(): void {
  filters.setting_name = "";
  currentPage.value = 1;
  fetchSettings();
}

function openCreateDialog(): void {
  editingId.value = null;
  resetFormValues();
  dialogVisible.value = true;
}

function openEditDialog(row: SettingPublic): void {
  editingId.value = row.id;
  form.setting_name = row.setting_name;
  form.setting_group = row.setting_group;
  form.setting_value = row.is_sensitive ? "" : (row.setting_value ?? "");
  form.description = row.description ?? "";
  form.value_type = row.value_type;
  form.is_sensitive = row.is_sensitive;
  form.is_encrypted = row.is_encrypted;
  form.is_readonly = row.is_readonly;
  dialogVisible.value = true;
}

async function submitForm(): Promise<void> {
  const formInstance = formRef.value;
  if (!formInstance) return;
  await formInstance.validate();

  saving.value = true;
  try {
    if (isEdit.value && editingId.value !== null) {
      await settingsApi.update(editingId.value, {
        setting_value: form.setting_value,
        setting_group: form.setting_group,
        description: form.description || null,
        value_type: form.value_type,
        is_sensitive: form.is_sensitive,
        is_encrypted: form.is_encrypted,
        is_readonly: form.is_readonly,
      });
      ElMessage.success("更新成功");
    } else {
      await settingsApi.create({
        setting_name: form.setting_name,
        setting_group: form.setting_group,
        setting_value: form.setting_value || null,
        description: form.description || null,
        value_type: form.value_type,
        is_sensitive: form.is_sensitive,
        is_encrypted: form.is_encrypted,
        is_readonly: form.is_readonly,
      });
      ElMessage.success("创建成功");
    }

    dialogVisible.value = false;
    await fetchGroups();
    if (form.setting_group) {
      activeGroup.value = form.setting_group;
    }
    await fetchSettings();
  } catch {
    ElMessage.error("保存失败，请检查配置值类型");
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  await fetchGroups();
  await fetchSettings();
});
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-form {
  margin-bottom: 16px;
}

.attr-tag {
  margin-left: 6px;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
