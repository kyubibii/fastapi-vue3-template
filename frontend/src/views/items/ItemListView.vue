<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>物品管理</span>
          <div>
            <el-button
              v-if="permStore.hasPermission('content.items.export')"
              @click="exportCsv"
            >
              导出 CSV
            </el-button>
            <el-button
              v-if="permStore.hasPermission('content.items.create')"
              type="primary"
              @click="router.push('/items/create')"
            >
              新建物品
            </el-button>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="title" label="标题" />
        <el-table-column
          prop="description"
          label="描述"
          show-overflow-tooltip
        />
        <el-table-column
          prop="created_at"
          label="创建时间"
          :formatter="fmtDate"
        />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button
              v-if="permStore.hasPermission('content.items.update')"
              size="small"
              @click="router.push(`/items/${row.id}/edit`)"
            >
              编辑
            </el-button>
            <el-popconfirm
              v-if="permStore.hasPermission('content.items.delete')"
              title="确认删除？"
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
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @change="fetchItems"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { itemsApi } from "@/api/items";
import type { ItemPublic } from "@/api/items";
import { usePermissionStore } from "@/stores/permission";

const router = useRouter();
const permStore = usePermissionStore();

const loading = ref(false);
const items = ref<ItemPublic[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

function fmtDate(_row: unknown, _col: unknown, val: string) {
  return val ? new Date(val).toLocaleString("zh-CN") : "—";
}

async function fetchItems() {
  loading.value = true;
  try {
    const skip = (currentPage.value - 1) * pageSize.value;
    const res = await itemsApi.list({ skip, limit: pageSize.value });
    items.value = res.data.data;
    total.value = res.data.count;
  } catch {
    ElMessage.error("加载物品列表失败");
  } finally {
    loading.value = false;
  }
}

async function deleteItem(id: string) {
  try {
    await itemsApi.delete(id);
    ElMessage.success("删除成功");
    fetchItems();
  } catch {
    ElMessage.error("删除失败");
  }
}

async function exportCsv() {
  try {
    const res = await itemsApi.exportCsv();
    const url = URL.createObjectURL(res.data as Blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "items.csv";
    a.click();
    URL.revokeObjectURL(url);
  } catch {
    ElMessage.error("导出失败");
  }
}

onMounted(fetchItems);
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
