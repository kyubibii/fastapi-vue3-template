<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button
            v-if="permStore.hasPermission('user_mgmt.users.create')"
            type="primary"
            @click="router.push('/users/create')"
          >
            新建用户
          </el-button>
        </div>
      </template>

      <el-form inline class="filter-form">
        <el-form-item label="用户名">
          <el-input
            v-model="filters.username"
            placeholder="请输入用户名"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input
            v-model="filters.email"
            placeholder="请输入邮箱"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.is_active" placeholder="全部" clearable>
            <el-option label="正常" value="true" />
            <el-option label="禁用" value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="性别">
          <el-select
            v-model="filters.gender"
            placeholder="全部"
            clearable
            style="width: 120px"
          >
            <el-option
              v-for="opt in GENDER_OPTIONS"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select
            v-model="filters.role_ids"
            multiple
            filterable
            clearable
            collapse-tags
            collapse-tags-tooltip
            placeholder="请选择角色"
            style="width: 240px"
          >
            <el-option
              v-for="role in roleOptions"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="users" stripe>
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="nickname" label="昵称" />
        <el-table-column label="性别" width="90" align="center">
          <template #default="{ row }">
            <span v-if="row.gender">{{ genderLabel(row.gender) }}</span>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? "正常" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色">
          <template #default="{ row }">
            <div v-if="row.roles.length" class="role-tags">
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
        <el-table-column
          prop="created_at"
          label="创建时间"
          :formatter="fmtDate"
        />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="permStore.hasPermission('user_mgmt.users.update')"
              size="small"
              @click="router.push(`/users/${row.id}/edit`)"
            >
              编辑
            </el-button>
            <el-popconfirm
              v-if="permStore.hasPermission('user_mgmt.users.delete')"
              title="确认删除该用户？"
              @confirm="deleteUser(row.id)"
            >
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @change="fetchUsers"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { usersApi } from "@/api/users";
import type { UserPublic } from "@/api/users";
import { rolesApi } from "@/api/rbac";
import type { RolePublic } from "@/api/rbac";
import { GENDER_OPTIONS, GENDER_LABELS, type GenderValue } from "@/constants";
import { usePermissionStore } from "@/stores/permission";

const router = useRouter();
const permStore = usePermissionStore();

const loading = ref(false);
const users = ref<UserPublic[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const roleOptions = ref<RolePublic[]>([]);
const filters = reactive({
  username: "",
  email: "",
  is_active: "" as "" | "true" | "false",
  role_ids: [] as number[],
  gender: "" as "" | GenderValue,
});

function fmtDate(_row: unknown, _col: unknown, val: string) {
  return val ? new Date(val).toLocaleString("zh-CN") : "—";
}

function genderLabel(gender: GenderValue) {
  return GENDER_LABELS[gender];
}

async function fetchUsers() {
  loading.value = true;
  try {
    const skip = (currentPage.value - 1) * pageSize.value;
    const res = await usersApi.list({
      skip,
      limit: pageSize.value,
      username: filters.username || undefined,
      email: filters.email || undefined,
      is_active:
        filters.is_active === "" ? undefined : filters.is_active === "true",
      role_ids: filters.role_ids.length ? filters.role_ids : undefined,
      gender: filters.gender || undefined,
    });
    users.value = res.data.data;
    total.value = res.data.count;
  } catch {
    ElMessage.error("加载用户列表失败");
  } finally {
    loading.value = false;
  }
}

async function deleteUser(id: string) {
  try {
    await usersApi.delete(id);
    ElMessage.success("删除成功");
    fetchUsers();
  } catch {
    ElMessage.error("删除失败");
  }
}

async function fetchRoles() {
  try {
    const res = await rolesApi.list();
    roleOptions.value = res.data.data;
  } catch {
    ElMessage.error("加载角色选项失败");
  }
}

function handleSearch() {
  currentPage.value = 1;
  fetchUsers();
}

function resetFilters() {
  filters.username = "";
  filters.email = "";
  filters.is_active = "";
  filters.role_ids = [];
  filters.gender = "";
  currentPage.value = 1;
  fetchUsers();
}

onMounted(async () => {
  await fetchRoles();
  await fetchUsers();
});
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filter-form {
  margin-bottom: 16px;
}
.role-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
