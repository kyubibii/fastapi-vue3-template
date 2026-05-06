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

          <el-divider />

          <div class="card-header user-section-header">
            <span>「{{ selectedRole.name }}」用户分配</span>
            <el-button
              type="primary"
              size="small"
              :loading="savingUsers"
              @click="saveRoleUsers"
            >
              保存用户分配
            </el-button>
          </div>

          <div class="assigned-user-section">
            <div class="section-title">已分配用户</div>
            <div v-if="assignedUsers.length" class="assigned-user-list">
              <el-tag
                v-for="user in assignedUsers"
                :key="user.id"
                closable
                class="assigned-user-tag"
                @close="removeAssignedUser(user.id)"
              >
                {{ user.nickname || user.username }}
              </el-tag>
            </div>
            <el-empty v-else description="当前角色还没有分配用户" />
          </div>

          <el-form inline class="user-search-form">
            <el-form-item label="搜索用户">
              <el-input
                v-model="userKeyword"
                placeholder="用户名 / 昵称 / 邮箱"
                clearable
                @keyup.enter="searchAssignableUsers"
              />
            </el-form-item>
            <el-form-item>
              <el-button @click="searchAssignableUsers">查询</el-button>
              <el-button @click="resetUserSearch">重置</el-button>
              <el-button
                type="primary"
                :disabled="!selectedAssignableUsers.length"
                @click="appendSelectedUsers"
              >
                添加选中用户
              </el-button>
            </el-form-item>
          </el-form>

          <el-table
            v-loading="loadingAssignableUsers"
            :data="assignableUsers"
            row-key="id"
            size="small"
            @selection-change="onAssignableSelectionChange"
          >
            <el-table-column type="selection" width="48" />
            <el-table-column prop="username" label="用户名" min-width="140" />
            <el-table-column prop="nickname" label="昵称" min-width="140" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
            <el-table-column label="现有角色" min-width="180">
              <template #default="{ row }">
                <div v-if="row.roles.length" class="role-tag-list">
                  <el-tag
                    v-for="role in row.roles"
                    :key="role.id"
                    size="small"
                    type="info"
                  >
                    {{ role.name }}
                  </el-tag>
                </div>
                <span v-else>—</span>
              </template>
            </el-table-column>
          </el-table>
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
import { usersApi } from "@/api/users";
import type { UserSearchPublic } from "@/api/users";

const roles = ref<RolePublic[]>([]);
const selectedRole = ref<RolePublic | null>(null);
const treeRef = ref<InstanceType<typeof ElTree>>();
const treeData = ref<object[]>([]);
const checkedKeys = ref<string[]>([]);
const saving = ref(false);
const savingUsers = ref(false);
const showCreateRole = ref(false);
const newRole = ref({ name: "", code: "" });
const assignedUsers = ref<UserSearchPublic[]>([]);
const assignableUsers = ref<UserSearchPublic[]>([]);
const selectedAssignableUsers = ref<UserSearchPublic[]>([]);
const loadingAssignableUsers = ref(false);
const userKeyword = ref("");

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
  permIdKeyMap.clear();
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
  const roleId = parseInt(index, 10);
  selectedRole.value = roles.value.find((r) => r.id === roleId) ?? null;
  if (!selectedRole.value) return;
  const res = await rolesApi.getPermissions(roleId);
  checkedKeys.value = res.data.map((id: number) => permIdKeyMap.get(id) ?? "");
  // Set checked state on tree
  treeRef.value?.setCheckedKeys(checkedKeys.value);
  await loadRoleUsers(roleId);
  assignableUsers.value = [];
  selectedAssignableUsers.value = [];
  userKeyword.value = "";
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

async function loadRoleUsers(roleId: number) {
  try {
    const res = await rolesApi.getUsers(roleId);
    assignedUsers.value = res.data.data;
  } catch {
    ElMessage.error("加载角色用户失败");
  }
}

async function searchAssignableUsers() {
  if (!selectedRole.value) return;
  loadingAssignableUsers.value = true;
  try {
    const res = await usersApi.search({
      keyword: userKeyword.value || undefined,
      exclude_role_id: selectedRole.value.id,
      limit: 50,
    });
    const assignedIds = new Set(assignedUsers.value.map((user) => user.id));
    assignableUsers.value = res.data.data.filter(
      (user) => !assignedIds.has(user.id),
    );
  } catch {
    ElMessage.error("搜索用户失败");
  } finally {
    loadingAssignableUsers.value = false;
  }
}

function onAssignableSelectionChange(selection: UserSearchPublic[]) {
  selectedAssignableUsers.value = selection;
}

function appendSelectedUsers() {
  const assignedIds = new Set(assignedUsers.value.map((user) => user.id));
  const incomingUsers = selectedAssignableUsers.value.filter(
    (user) => !assignedIds.has(user.id),
  );
  assignedUsers.value = [...assignedUsers.value, ...incomingUsers];
  assignableUsers.value = assignableUsers.value.filter(
    (user) => !incomingUsers.some((selected) => selected.id === user.id),
  );
  selectedAssignableUsers.value = [];
}

function removeAssignedUser(userId: string) {
  assignedUsers.value = assignedUsers.value.filter(
    (user) => user.id !== userId,
  );
}

async function saveRoleUsers() {
  if (!selectedRole.value) return;
  savingUsers.value = true;
  try {
    await rolesApi.assignUsers(
      selectedRole.value.id,
      assignedUsers.value.map((user) => user.id),
    );
    ElMessage.success("角色用户保存成功");
    await loadRoleUsers(selectedRole.value.id);
    await searchAssignableUsers();
  } catch {
    ElMessage.error("角色用户保存失败");
  } finally {
    savingUsers.value = false;
  }
}

function resetUserSearch() {
  userKeyword.value = "";
  selectedAssignableUsers.value = [];
  searchAssignableUsers();
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

.user-section-header {
  margin-bottom: 12px;
}

.assigned-user-section {
  margin-bottom: 16px;
}

.section-title {
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.assigned-user-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.assigned-user-tag {
  margin-bottom: 4px;
}

.user-search-form {
  margin-bottom: 16px;
}

.role-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
