<template>
  <div>
    <el-row :gutter="20">
      <!-- Role list -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>角色列表</span>
              <el-button
                size="small"
                type="primary"
                @click="showCreateRole = true"
                >新建</el-button
              >
            </div>
          </template>
          <el-menu @select="onSelectRole">
            <el-menu-item
              v-for="role in roles"
              :key="role.id"
              :index="String(role.id)"
            >
              {{ role.name }}
              <el-tag
                v-if="role.is_builtin"
                size="small"
                type="warning"
                style="margin-left: 8px"
                >内置</el-tag
              >
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- Permission tree -->
      <el-col :span="16">
        <el-card v-if="selectedRole">
          <template #header>
            <div class="card-header">
              <span>「{{ selectedRole.name }}」权限配置</span>
              <el-button
                type="primary"
                size="small"
                :loading="saving"
                @click="savePermissions"
              >
                保存
              </el-button>
            </div>
          </template>

          <el-tree
            ref="treeRef"
            :data="treeData"
            show-checkbox
            node-key="key"
            :props="treeProps"
            :default-checked-keys="checkedKeys"
          />
        </el-card>
        <el-empty v-else description="请选择一个角色" />
      </el-col>
    </el-row>

    <!-- Create role dialog -->
    <el-dialog v-model="showCreateRole" title="新建角色" width="400px">
      <el-form :model="newRole" label-width="80px">
        <el-form-item label="角色名">
          <el-input v-model="newRole.name" />
        </el-form-item>
        <el-form-item label="角色编码">
          <el-input v-model="newRole.code" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateRole = false">取消</el-button>
        <el-button type="primary" @click="createRole">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import type { ElTree } from "element-plus";
import { rolesApi, permissionsApi } from "@/api/rbac";
import type { RolePublic, PermissionTreeResponse } from "@/api/rbac";

const roles = ref<RolePublic[]>([]);
const selectedRole = ref<RolePublic | null>(null);
const treeRef = ref<InstanceType<typeof ElTree>>();
const treeData = ref<object[]>([]);
const checkedKeys = ref<string[]>([]);
const saving = ref(false);
const showCreateRole = ref(false);
const newRole = ref({ name: "", code: "" });

const treeProps = { label: "label", children: "children" };

// Map perm id → key in tree
const permIdKeyMap = new Map<number, string>();

async function fetchRoles() {
  const res = await rolesApi.list();
  roles.value = res.data.data;
}

async function fetchPermTree() {
  const res = await permissionsApi.tree();
  const data = res.data as PermissionTreeResponse;
  // Build el-tree compatible structure
  treeData.value = data.groups.map((g) => ({
    key: `group-${g.id}`,
    label: g.name,
    children: g.pages.map((p) => ({
      key: `page-${p.id}`,
      label: p.name,
      children: p.permissions.map((perm) => {
        const key = `perm-${perm.id}`;
        permIdKeyMap.set(perm.id, key);
        return { key, label: perm.name, permId: perm.id };
      }),
    })),
  }));
}

async function onSelectRole(index: string) {
  const roleId = parseInt(index);
  selectedRole.value = roles.value.find((r) => r.id === roleId) ?? null;
  if (!selectedRole.value) return;
  const res = await rolesApi.getPermissions(roleId);
  checkedKeys.value = res.data.map((id: number) => permIdKeyMap.get(id) ?? "");
  // Set checked state on tree
  treeRef.value?.setCheckedKeys(checkedKeys.value);
}

async function savePermissions() {
  if (!selectedRole.value || !treeRef.value) return;
  saving.value = true;
  try {
    const checked = treeRef.value.getCheckedNodes(true) as {
      permId?: number;
    }[];
    const permIds = checked
      .filter((n) => n.permId)
      .map((n) => n.permId as number);
    await rolesApi.assignPermissions(selectedRole.value.id, permIds);
    ElMessage.success("权限保存成功");
  } catch {
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
}

async function createRole() {
  if (!newRole.value.name || !newRole.value.code) {
    ElMessage.warning("请填写角色名和编码");
    return;
  }
  try {
    await rolesApi.create(newRole.value);
    ElMessage.success("创建成功");
    showCreateRole.value = false;
    newRole.value = { name: "", code: "" };
    fetchRoles();
  } catch {
    ElMessage.error("创建失败，编码可能重复");
  }
}

onMounted(async () => {
  await Promise.all([fetchRoles(), fetchPermTree()]);
});
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
