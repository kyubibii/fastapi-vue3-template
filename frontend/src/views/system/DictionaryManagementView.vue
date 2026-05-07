<template>
  <div class="dictionary-page">
    <el-card class="type-card">
      <template #header>
        <div class="card-header">
          <span>数据字典类型</span>
          <el-button
            v-if="permStore.hasPermission('system.dictionaries.create')"
            type="primary"
            @click="openTypeCreateDialog"
          >
            新增类型
          </el-button>
        </div>
      </template>

      <el-form inline class="filter-form">
        <el-form-item label="类型编码">
          <el-input
            v-model="typeFilters.type_code"
            placeholder="请输入类型编码"
            clearable
            @keyup.enter="handleTypeSearch"
          />
        </el-form-item>
        <el-form-item label="类型名称">
          <el-input
            v-model="typeFilters.type_name"
            placeholder="请输入类型名称"
            clearable
            @keyup.enter="handleTypeSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleTypeSearch">查询</el-button>
          <el-button @click="resetTypeFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="typeLoading"
        :data="types"
        stripe
        highlight-current-row
        :current-row-key="selectedTypeId ?? undefined"
        row-key="id"
        @current-change="handleTypeRowChange"
        @row-click="handleTypeRowClick"
      >
        <el-table-column prop="type_code" label="编码" min-width="180" />
        <el-table-column prop="type_name" label="名称" min-width="180" />
        <el-table-column
          prop="description"
          label="说明"
          min-width="220"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span>{{ row.description || "—" }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="100" />
        <el-table-column
          prop="updated_at"
          label="更新时间"
          width="180"
          :formatter="fmtDate"
        />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="permStore.hasPermission('system.dictionaries.update')"
              size="small"
              @click="openTypeEditDialog(row)"
            >
              编辑
            </el-button>
            <el-popconfirm
              v-if="permStore.hasPermission('system.dictionaries.delete')"
              title="确认删除该字典类型？"
              @confirm="deleteType(row.id)"
            >
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        :current-page="typeCurrentPage"
        :page-size="typePageSize"
        :total="typeTotal"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @update:current-page="handleTypeCurrentPageChange"
        @update:page-size="handleTypePageSizeChange"
        @change="fetchTypes"
      />
    </el-card>

    <el-card class="item-card">
      <template #header>
        <div class="card-header">
          <div>
            <span>字典项</span>
            <span class="selected-type" v-if="selectedTypeName">
              （当前类型：{{ selectedTypeName }}）
            </span>
          </div>
          <el-button
            v-if="permStore.hasPermission('system.dictionaries.create')"
            type="primary"
            :disabled="!selectedTypeId"
            @click="openItemCreateDialog"
          >
            新增字典项
          </el-button>
        </div>
      </template>

      <el-form inline class="filter-form">
        <el-form-item label="项编码">
          <el-input
            v-model="itemFilters.item_code"
            placeholder="请输入项编码"
            clearable
            @keyup.enter="handleItemSearch"
          />
        </el-form-item>
        <el-form-item label="项名称">
          <el-input
            v-model="itemFilters.item_label"
            placeholder="请输入项名称"
            clearable
            @keyup.enter="handleItemSearch"
          />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-select v-model="itemFilters.enabled" placeholder="全部" clearable>
            <el-option label="启用" value="true" />
            <el-option label="禁用" value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleItemSearch">查询</el-button>
          <el-button @click="resetItemFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="itemLoading" :data="items" stripe>
        <el-table-column prop="item_code" label="编码" min-width="160" />
        <el-table-column prop="item_label" label="名称" min-width="180" />
        <el-table-column
          prop="item_value"
          label="值"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column prop="sort_order" label="排序" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">
              {{ row.enabled ? "启用" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="updated_at"
          label="更新时间"
          width="180"
          :formatter="fmtDate"
        />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="permStore.hasPermission('system.dictionaries.update')"
              size="small"
              @click="openItemEditDialog(row)"
            >
              编辑
            </el-button>
            <el-popconfirm
              v-if="permStore.hasPermission('system.dictionaries.delete')"
              title="确认删除该字典项？"
              @confirm="deleteItem(row.id)"
            >
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        :current-page="itemCurrentPage"
        :page-size="itemPageSize"
        :total="itemTotal"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @update:current-page="handleItemCurrentPageChange"
        @update:page-size="handleItemPageSizeChange"
        @change="fetchItems"
      />
    </el-card>

    <el-dialog
      v-model="typeDialogVisible"
      :title="typeIsEdit ? '编辑字典类型' : '新增字典类型'"
      width="640px"
      destroy-on-close
    >
      <el-form
        ref="typeFormRef"
        :model="typeForm"
        :rules="typeRules"
        label-width="110px"
      >
        <el-form-item label="类型编码" prop="type_code">
          <el-input
            v-model="typeForm.type_code"
            placeholder="如: order_status"
          />
        </el-form-item>
        <el-form-item label="类型名称" prop="type_name">
          <el-input v-model="typeForm.type_name" placeholder="如: 订单状态" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="typeForm.sort_order" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="说明" prop="description">
          <el-input v-model="typeForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="typeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="typeSaving" @click="submitTypeForm">
          保存
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="itemDialogVisible"
      :title="itemIsEdit ? '编辑字典项' : '新增字典项'"
      width="640px"
      destroy-on-close
    >
      <el-form
        ref="itemFormRef"
        :model="itemForm"
        :rules="itemRules"
        label-width="110px"
      >
        <el-form-item label="项编码" prop="item_code">
          <el-input v-model="itemForm.item_code" placeholder="如: paid" />
        </el-form-item>
        <el-form-item label="项名称" prop="item_label">
          <el-input v-model="itemForm.item_label" placeholder="如: 已支付" />
        </el-form-item>
        <el-form-item label="项值" prop="item_value">
          <el-input v-model="itemForm.item_value" placeholder="如: PAID" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="itemForm.sort_order" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="是否启用" prop="enabled">
          <el-switch v-model="itemForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="itemSaving" @click="submitItemForm">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import {
  dictionaryApi,
  type DictionaryItemPublic,
  type DictionaryTypePublic,
} from "../../api/dictionary";
import { usePermissionStore } from "../../stores/permission";

const permStore = usePermissionStore();

const typeLoading = ref(false);
const types = ref<DictionaryTypePublic[]>([]);
const typeTotal = ref(0);
const typeCurrentPage = ref(1);
const typePageSize = ref(10);
const typeFilters = reactive({
  type_code: "",
  type_name: "",
});

const selectedTypeId = ref<string | null>(null);

const itemLoading = ref(false);
const items = ref<DictionaryItemPublic[]>([]);
const itemTotal = ref(0);
const itemCurrentPage = ref(1);
const itemPageSize = ref(10);
const itemFilters = reactive({
  item_code: "",
  item_label: "",
  enabled: "" as "" | "true" | "false",
});

const typeDialogVisible = ref(false);
const typeSaving = ref(false);
const typeEditingId = ref<string | null>(null);
const typeFormRef = ref<FormInstance>();
const typeForm = reactive({
  type_code: "",
  type_name: "",
  sort_order: 0,
  description: "",
});

const itemDialogVisible = ref(false);
const itemSaving = ref(false);
const itemEditingId = ref<string | null>(null);
const itemFormRef = ref<FormInstance>();
const itemForm = reactive({
  item_code: "",
  item_label: "",
  item_value: "",
  sort_order: 0,
  enabled: true,
});

const typeIsEdit = computed(() => !!typeEditingId.value);
const itemIsEdit = computed(() => !!itemEditingId.value);
const selectedTypeName = computed(() => {
  if (!selectedTypeId.value) return "";
  const row = types.value.find((item) => item.id === selectedTypeId.value);
  return row?.type_name ?? "";
});

const typeRules: FormRules = {
  type_code: [
    { required: true, message: "请输入类型编码", trigger: "blur" },
    { min: 1, max: 100, message: "长度需在 1-100 之间", trigger: "blur" },
  ],
  type_name: [
    { required: true, message: "请输入类型名称", trigger: "blur" },
    { min: 1, max: 100, message: "长度需在 1-100 之间", trigger: "blur" },
  ],
};

const itemRules: FormRules = {
  item_code: [
    { required: true, message: "请输入项编码", trigger: "blur" },
    { min: 1, max: 100, message: "长度需在 1-100 之间", trigger: "blur" },
  ],
  item_label: [
    { required: true, message: "请输入项名称", trigger: "blur" },
    { min: 1, max: 200, message: "长度需在 1-200 之间", trigger: "blur" },
  ],
  item_value: [
    { required: true, message: "请输入项值", trigger: "blur" },
    { min: 1, max: 500, message: "长度需在 1-500 之间", trigger: "blur" },
  ],
};

function fmtDate(_row: unknown, _col: unknown, val: string | null) {
  return val ? new Date(val).toLocaleString("zh-CN") : "—";
}

function resetTypeFormValues(): void {
  typeForm.type_code = "";
  typeForm.type_name = "";
  typeForm.sort_order = 0;
  typeForm.description = "";
}

function resetItemFormValues(): void {
  itemForm.item_code = "";
  itemForm.item_label = "";
  itemForm.item_value = "";
  itemForm.sort_order = 0;
  itemForm.enabled = true;
}

function ensureSelectedType(): void {
  if (!types.value.length) {
    selectedTypeId.value = null;
    return;
  }

  const exists = types.value.some((item) => item.id === selectedTypeId.value);
  if (!exists) {
    selectedTypeId.value = types.value[0].id;
  }
}

async function fetchTypes(): Promise<void> {
  typeLoading.value = true;
  try {
    const skip = (typeCurrentPage.value - 1) * typePageSize.value;
    const res = await dictionaryApi.listTypes({
      skip,
      limit: typePageSize.value,
      type_code: typeFilters.type_code || undefined,
      type_name: typeFilters.type_name || undefined,
    });
    types.value = res.data.data;
    typeTotal.value = res.data.count;
    ensureSelectedType();
    await fetchItems();
  } catch {
    ElMessage.error("加载字典类型失败");
  } finally {
    typeLoading.value = false;
  }
}

async function fetchItems(): Promise<void> {
  if (!selectedTypeId.value) {
    items.value = [];
    itemTotal.value = 0;
    return;
  }

  itemLoading.value = true;
  try {
    const skip = (itemCurrentPage.value - 1) * itemPageSize.value;
    const res = await dictionaryApi.listItems({
      skip,
      limit: itemPageSize.value,
      type_id: selectedTypeId.value,
      item_code: itemFilters.item_code || undefined,
      item_label: itemFilters.item_label || undefined,
      enabled:
        itemFilters.enabled === "" ? undefined : itemFilters.enabled === "true",
    });
    items.value = res.data.data;
    itemTotal.value = res.data.count;
  } catch {
    ElMessage.error("加载字典项失败");
  } finally {
    itemLoading.value = false;
  }
}

function handleTypeSearch(): void {
  typeCurrentPage.value = 1;
  fetchTypes();
}

function handleTypeCurrentPageChange(page: number): void {
  typeCurrentPage.value = page;
}

function handleTypePageSizeChange(size: number): void {
  typePageSize.value = size;
}

function resetTypeFilters(): void {
  typeFilters.type_code = "";
  typeFilters.type_name = "";
  typeCurrentPage.value = 1;
  fetchTypes();
}

function handleItemSearch(): void {
  itemCurrentPage.value = 1;
  fetchItems();
}

function handleItemCurrentPageChange(page: number): void {
  itemCurrentPage.value = page;
}

function handleItemPageSizeChange(size: number): void {
  itemPageSize.value = size;
}

function resetItemFilters(): void {
  itemFilters.item_code = "";
  itemFilters.item_label = "";
  itemFilters.enabled = "";
  itemCurrentPage.value = 1;
  fetchItems();
}

function handleTypeRowChange(row: DictionaryTypePublic | undefined): void {
  if (!row) return;
  selectedTypeId.value = row.id;
  itemCurrentPage.value = 1;
  fetchItems();
}

function handleTypeRowClick(row: DictionaryTypePublic): void {
  selectedTypeId.value = row.id;
  itemCurrentPage.value = 1;
  fetchItems();
}

function openTypeCreateDialog(): void {
  typeEditingId.value = null;
  resetTypeFormValues();
  typeDialogVisible.value = true;
}

function openTypeEditDialog(row: DictionaryTypePublic): void {
  typeEditingId.value = row.id;
  typeForm.type_code = row.type_code;
  typeForm.type_name = row.type_name;
  typeForm.sort_order = row.sort_order;
  typeForm.description = row.description ?? "";
  typeDialogVisible.value = true;
}

async function submitTypeForm(): Promise<void> {
  const formInstance = typeFormRef.value;
  if (!formInstance) return;
  const valid = await formInstance.validate().catch(() => false);
  if (!valid) return;

  typeSaving.value = true;
  try {
    const payload = {
      type_code: typeForm.type_code,
      type_name: typeForm.type_name,
      sort_order: typeForm.sort_order,
      description: typeForm.description || null,
    };

    if (typeIsEdit.value && typeEditingId.value) {
      await dictionaryApi.updateType(typeEditingId.value, payload);
      ElMessage.success("类型更新成功");
    } else {
      await dictionaryApi.createType(payload);
      ElMessage.success("类型创建成功");
    }

    typeDialogVisible.value = false;
    await fetchTypes();
  } catch {
    ElMessage.error("保存类型失败");
  } finally {
    typeSaving.value = false;
  }
}

async function deleteType(id: string): Promise<void> {
  try {
    await dictionaryApi.deleteType(id);
    ElMessage.success("类型删除成功");
    await fetchTypes();
  } catch {
    ElMessage.error("删除类型失败");
  }
}

function openItemCreateDialog(): void {
  if (!selectedTypeId.value) {
    ElMessage.warning("请先选择字典类型");
    return;
  }
  itemEditingId.value = null;
  resetItemFormValues();
  itemDialogVisible.value = true;
}

function openItemEditDialog(row: DictionaryItemPublic): void {
  itemEditingId.value = row.id;
  itemForm.item_code = row.item_code;
  itemForm.item_label = row.item_label;
  itemForm.item_value = row.item_value;
  itemForm.sort_order = row.sort_order;
  itemForm.enabled = row.enabled;
  itemDialogVisible.value = true;
}

async function submitItemForm(): Promise<void> {
  if (!selectedTypeId.value) {
    ElMessage.warning("请先选择字典类型");
    return;
  }

  const formInstance = itemFormRef.value;
  if (!formInstance) return;
  const valid = await formInstance.validate().catch(() => false);
  if (!valid) return;

  itemSaving.value = true;
  try {
    const payload = {
      type_id: selectedTypeId.value,
      item_code: itemForm.item_code,
      item_label: itemForm.item_label,
      item_value: itemForm.item_value,
      sort_order: itemForm.sort_order,
      enabled: itemForm.enabled,
    };

    if (itemIsEdit.value && itemEditingId.value) {
      await dictionaryApi.updateItem(itemEditingId.value, payload);
      ElMessage.success("字典项更新成功");
    } else {
      await dictionaryApi.createItem(payload);
      ElMessage.success("字典项创建成功");
    }

    itemDialogVisible.value = false;
    await fetchItems();
  } catch {
    ElMessage.error("保存字典项失败");
  } finally {
    itemSaving.value = false;
  }
}

async function deleteItem(id: string): Promise<void> {
  try {
    await dictionaryApi.deleteItem(id);
    ElMessage.success("字典项删除成功");
    await fetchItems();
  } catch {
    ElMessage.error("删除字典项失败");
  }
}

onMounted(async () => {
  await fetchTypes();
});
</script>

<style scoped>
.dictionary-page {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-form {
  margin-bottom: 16px;
}

.selected-type {
  color: #64748b;
  margin-left: 8px;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

@media (max-width: 960px) {
  .card-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }
}
</style>
