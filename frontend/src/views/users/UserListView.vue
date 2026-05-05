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

      <el-table v-loading="loading" :data="users" stripe>
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="nickname" label="昵称" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? "正常" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="超管">
          <template #default="{ row }">
            <el-tag v-if="row.is_superuser" type="warning">是</el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="created_at"
          label="创建时间"
          :formatter="fmtDate"
        />
        <el-table-column label="操作" width="160">
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
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { usersApi } from "@/api/users";
import type { UserPublic } from "@/api/users";
import { usePermissionStore } from "@/stores/permission";

const router = useRouter();
const permStore = usePermissionStore();

const loading = ref(false);
const users = ref<UserPublic[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

function fmtDate(_row: unknown, _col: unknown, val: string) {
  return val ? new Date(val).toLocaleString("zh-CN") : "—";
}

async function fetchUsers() {
  loading.value = true;
  try {
    const skip = (currentPage.value - 1) * pageSize.value;
    const res = await usersApi.list({ skip, limit: pageSize.value });
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

onMounted(fetchUsers);
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
