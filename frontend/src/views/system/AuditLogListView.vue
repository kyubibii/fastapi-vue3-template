<template>
  <div>
    <el-card>
      <template #header>
        <span>操作日志</span>
      </template>

      <!-- Filters -->
      <el-form inline class="filter-form">
        <el-form-item label="接口路径">
          <el-input
            v-model="filters.endpoint"
            placeholder="/api/v1/..."
            clearable
          />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchLogs">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="logs" stripe size="small">
        <el-table-column prop="http_method" label="方法" width="80">
          <template #default="{ row }">
            <el-tag :type="methodType(row.http_method)" size="small">{{
              row.http_method
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="endpoint" label="接口" show-overflow-tooltip />
        <el-table-column prop="status_code" label="状态码" width="90">
          <template #default="{ row }">
            <el-tag
              :type="row.status_code < 400 ? 'success' : 'danger'"
              size="small"
            >
              {{ row.status_code }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="ip_address" label="IP" width="140" />
        <el-table-column prop="created_at" label="时间" :formatter="fmtDate" />
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @change="fetchLogs"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { auditLogsApi } from "@/api/auditLogs";
import type { AuditLogPublic } from "@/api/auditLogs";

const loading = ref(false);
const logs = ref<AuditLogPublic[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(50);
const dateRange = ref<[string, string] | null>(null);

const filters = reactive({ endpoint: "" });

function fmtDate(_row: unknown, _col: unknown, val: string) {
  return val ? new Date(val).toLocaleString("zh-CN") : "—";
}

function methodType(method: string) {
  const map: Record<string, string> = {
    GET: "info",
    POST: "success",
    PUT: "warning",
    PATCH: "warning",
    DELETE: "danger",
  };
  return map[method] ?? "info";
}

async function fetchLogs() {
  loading.value = true;
  try {
    const skip = (currentPage.value - 1) * pageSize.value;
    const res = await auditLogsApi.list({
      skip,
      limit: pageSize.value,
      endpoint: filters.endpoint || undefined,
      start_time: dateRange.value?.[0],
      end_time: dateRange.value?.[1],
    });
    logs.value = res.data.data;
    total.value = res.data.count;
  } catch {
    ElMessage.error("加载日志失败");
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.endpoint = "";
  dateRange.value = null;
  fetchLogs();
}

onMounted(fetchLogs);
</script>

<style scoped>
.filter-form {
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
