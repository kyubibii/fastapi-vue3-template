<template>
  <div>
    <el-card>
      <template #header>
        <span>操作日志</span>
      </template>

      <el-form inline class="filter-form">
        <el-form-item label="模块">
          <el-select
            v-model="filters.module"
            placeholder="请选择模块"
            clearable
            style="width: 180px"
          >
            <el-option
              v-for="option in moduleOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="接口路径">
          <el-input
            v-model="filters.endpointSuffix"
            placeholder="例如 /login 或 /users"
            clearable
            @keyup.enter="handleSearch"
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
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="logs" stripe size="small">
        <el-table-column prop="http_method" label="方法" width="80">
          <template #default="{ row }">
            <el-tag :type="methodType(row.http_method)" size="small">
              {{ row.http_method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="模块" width="120">
          <template #default="{ row }">
            {{ moduleLabelMap[row.module ?? ""] ?? row.module ?? "—" }}
          </template>
        </el-table-column>
        <el-table-column prop="operation" label="操作标题" width="180" />
        <el-table-column prop="endpoint" label="接口" show-overflow-tooltip />
        <el-table-column prop="status_code" label="状态码" width="90">
          <template #default="{ row }">
            <el-tag
              :type="(row.status_code ?? 500) < 400 ? 'success' : 'danger'"
              size="small"
            >
              {{ row.status_code ?? "—" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="ip_address" label="IP" width="140" />
        <el-table-column prop="created_at" label="时间" :formatter="fmtDate" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openDetailDrawer(row)"
              >详情</el-button
            >
          </template>
        </el-table-column>
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

    <el-drawer
      v-model="detailDrawerVisible"
      direction="rtl"
      size="56%"
      :with-header="false"
      :destroy-on-close="true"
      class="detail-drawer"
    >
      <div v-if="selectedLog" class="drawer-content">
        <div class="drawer-header">
          <div>
            <div class="drawer-title">日志详情</div>
            <div class="drawer-subtitle">
              {{ selectedLog.http_method }} {{ selectedLog.endpoint }}
            </div>
          </div>
          <div class="drawer-meta">
            <el-tag :type="methodType(selectedLog.http_method)" size="small">
              {{ selectedLog.http_method }}
            </el-tag>
            <el-tag
              :type="
                (selectedLog.status_code ?? 500) < 400 ? 'success' : 'danger'
              "
              size="small"
            >
              {{ selectedLog.status_code ?? "—" }}
            </el-tag>
          </div>
        </div>

        <div class="drawer-basic-info">
          <div class="info-item">
            <span class="info-label">模块</span>
            <span class="info-value">{{
              moduleLabelMap[selectedLog.module ?? ""] ??
              selectedLog.module ??
              "—"
            }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">操作</span>
            <span class="info-value">{{ selectedLog.operation || "—" }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">用户</span>
            <span class="info-value">{{ selectedLog.username || "—" }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">时间</span>
            <span class="info-value">{{
              fmtDate(null, null, selectedLog.created_at)
            }}</span>
          </div>
        </div>

        <el-tabs class="detail-tabs">
          <el-tab-pane label="请求体">
            <div class="payload-panel">
              <template v-if="requestPreview.kind === 'json'">
                <el-tree
                  :data="requestPreview.tree"
                  node-key="id"
                  default-expand-all
                  :expand-on-click-node="false"
                  class="json-tree"
                >
                  <template #default="{ data }">
                    <div class="json-node">
                      <span v-if="data.key" class="json-key"
                        >{{ data.key }}:</span
                      >
                      <span
                        v-if="
                          data.valueType === 'object' ||
                          data.valueType === 'array'
                        "
                        class="json-struct"
                      >
                        {{ data.preview }}
                      </span>
                      <span
                        v-else
                        class="json-value"
                        :class="`json-value-${data.valueType}`"
                      >
                        {{ data.preview }}
                      </span>
                    </div>
                  </template>
                </el-tree>
              </template>
              <template v-else-if="requestPreview.kind === 'text'">
                <pre class="raw-payload">{{ requestPreview.text }}</pre>
              </template>
              <el-empty v-else description="无请求体" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="返回体">
            <div class="payload-panel">
              <template v-if="responsePreview.kind === 'json'">
                <el-tree
                  :data="responsePreview.tree"
                  node-key="id"
                  default-expand-all
                  :expand-on-click-node="false"
                  class="json-tree"
                >
                  <template #default="{ data }">
                    <div class="json-node">
                      <span v-if="data.key" class="json-key"
                        >{{ data.key }}:</span
                      >
                      <span
                        v-if="
                          data.valueType === 'object' ||
                          data.valueType === 'array'
                        "
                        class="json-struct"
                      >
                        {{ data.preview }}
                      </span>
                      <span
                        v-else
                        class="json-value"
                        :class="`json-value-${data.valueType}`"
                      >
                        {{ data.preview }}
                      </span>
                    </div>
                  </template>
                </el-tree>
              </template>
              <template v-else-if="responsePreview.kind === 'text'">
                <pre class="raw-payload">{{ responsePreview.text }}</pre>
              </template>
              <el-empty v-else description="无返回体" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="错误信息">
            <div class="payload-panel">
              <template v-if="selectedLog.error_message">
                <pre class="raw-payload error-payload">{{
                  selectedLog.error_message
                }}</pre>
              </template>
              <el-empty v-else description="无错误信息" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { auditLogsApi } from "@/api/auditLogs";
import type { AuditLogPublic } from "@/api/auditLogs";

type JsonValueType =
  | "object"
  | "array"
  | "string"
  | "number"
  | "boolean"
  | "null";

interface JsonTreeNode {
  id: string;
  key: string;
  preview: string;
  valueType: JsonValueType;
  children?: JsonTreeNode[];
}

type PayloadPreview =
  | { kind: "json"; tree: JsonTreeNode[] }
  | { kind: "text"; text: string }
  | { kind: "empty" };

const moduleOptions = [
  { label: "认证", value: "auth" },
  { label: "用户", value: "users" },
  { label: "物品", value: "items" },
  { label: "角色", value: "roles" },
  { label: "权限", value: "permissions" },
  { label: "日志", value: "audit-logs" },
];

const moduleLabelMap = Object.fromEntries(
  moduleOptions.map((option) => [option.value, option.label]),
);

const loading = ref(false);
const logs = ref<AuditLogPublic[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(50);
const dateRange = ref<[string, string] | null>(null);
const detailDrawerVisible = ref(false);
const selectedLog = ref<AuditLogPublic | null>(null);

const filters = reactive({ module: "", endpointSuffix: "" });

function fmtDate(_row: unknown, _col: unknown, val: string | null) {
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

function formatPrimitive(value: unknown) {
  if (typeof value === "string") {
    return `"${value}"`;
  }
  if (value === null) {
    return "null";
  }
  return String(value);
}

function buildJsonNode(key: string, value: unknown, id: string): JsonTreeNode {
  if (Array.isArray(value)) {
    return {
      id,
      key,
      preview: `Array(${value.length})`,
      valueType: "array",
      children: value.map((item, index) =>
        buildJsonNode(String(index), item, `${id}-${index}`),
      ),
    };
  }

  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    return {
      id,
      key,
      preview: `Object(${entries.length})`,
      valueType: "object",
      children: entries.map(([childKey, childValue]) =>
        buildJsonNode(childKey, childValue, `${id}-${childKey}`),
      ),
    };
  }

  if (value === null) {
    return { id, key, preview: "null", valueType: "null" };
  }

  if (typeof value === "string") {
    return { id, key, preview: formatPrimitive(value), valueType: "string" };
  }

  if (typeof value === "number") {
    return { id, key, preview: formatPrimitive(value), valueType: "number" };
  }

  return {
    id,
    key,
    preview: formatPrimitive(value),
    valueType: typeof value === "boolean" ? "boolean" : "string",
  };
}

function buildJsonTree(value: unknown): JsonTreeNode[] {
  if (Array.isArray(value)) {
    return value.map((item, index) =>
      buildJsonNode(String(index), item, `root-${index}`),
    );
  }

  if (value && typeof value === "object") {
    return Object.entries(value as Record<string, unknown>).map(
      ([key, childValue]) => buildJsonNode(key, childValue, `root-${key}`),
    );
  }

  return [buildJsonNode("value", value, "root-value")];
}

function buildPayloadPreview(payload: string | null): PayloadPreview {
  if (!payload) {
    return { kind: "empty" };
  }

  try {
    return {
      kind: "json",
      tree: buildJsonTree(JSON.parse(payload) as unknown),
    };
  } catch {
    return {
      kind: "text",
      text: payload,
    };
  }
}

const requestPreview = computed(() =>
  buildPayloadPreview(selectedLog.value?.request_body ?? null),
);

const responsePreview = computed(() =>
  buildPayloadPreview(selectedLog.value?.response_body ?? null),
);

async function fetchLogs() {
  loading.value = true;
  try {
    const skip = (currentPage.value - 1) * pageSize.value;
    const res = await auditLogsApi.list({
      skip,
      limit: pageSize.value,
      module: filters.module || undefined,
      endpoint: buildEndpointFilter(),
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

function buildEndpointFilter() {
  const suffix = filters.endpointSuffix.trim();
  if (!suffix) {
    return undefined;
  }
  if (!filters.module) {
    return suffix;
  }
  const normalizedSuffix = suffix.startsWith("/") ? suffix : `/${suffix}`;
  return `/api/v1/${filters.module}${normalizedSuffix}`;
}

function handleSearch() {
  currentPage.value = 1;
  fetchLogs();
}

function resetFilters() {
  filters.module = "";
  filters.endpointSuffix = "";
  dateRange.value = null;
  currentPage.value = 1;
  fetchLogs();
}

function openDetailDrawer(log: AuditLogPublic) {
  selectedLog.value = log;
  detailDrawerVisible.value = true;
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

.drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px 18px 12px;
  background: linear-gradient(180deg, #fcfcfd 0%, #f7f8fa 100%);
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.drawer-title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.drawer-subtitle {
  margin-top: 6px;
  color: var(--el-text-color-regular);
  word-break: break-all;
  font-family: Consolas, "Courier New", monospace;
  font-size: 13px;
}

.drawer-meta {
  display: flex;
  gap: 8px;
}

.drawer-basic-info {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 16px;
  margin-bottom: 14px;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  background: #fff;
}

.info-item {
  display: flex;
  gap: 8px;
  min-width: 0;
}

.info-label {
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.info-value {
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-tabs {
  flex: 1;
  min-height: 0;
  background: #fff;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  padding: 8px 12px 10px;
}

.payload-panel {
  min-height: 340px;
  max-height: 100%;
  overflow: auto;
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: #fbfbfc;
  padding: 12px;
}

.json-tree {
  background: transparent;
}

.json-node {
  display: inline-flex;
  gap: 6px;
  align-items: baseline;
  font-family: Consolas, "Courier New", monospace;
  font-size: 13px;
  line-height: 1.6;
}

.json-key {
  color: #881391;
}

.json-struct {
  color: #666;
}

.json-value-string {
  color: #c41a16;
}

.json-value-number {
  color: #1c00cf;
}

.json-value-boolean {
  color: #aa0d91;
}

.json-value-null {
  color: #808080;
}

.raw-payload {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: Consolas, "Courier New", monospace;
  font-size: 13px;
  line-height: 1.6;
}

.error-payload {
  color: #b42318;
}

@media (max-width: 900px) {
  :deep(.detail-drawer) {
    width: 100% !important;
  }

  .drawer-basic-info {
    grid-template-columns: 1fr;
  }
}
</style>
