<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>定时任务管理</span>
          <el-button :icon="Refresh" circle @click="loadJobs" />
        </div>
      </template>

      <el-table v-loading="loading" :data="jobs" stripe>
        <el-table-column prop="name" label="任务名称" min-width="200" />
        <el-table-column label="触发器类型" width="120">
          <template #default="{ row }">
            <el-tag :type="triggerTagType(row.trigger_type)" size="small">
              {{ row.trigger_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="trigger_description"
          label="触发配置"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column label="下次运行时间" width="180">
          <template #default="{ row }">
            <span>{{
              row.next_run_time ? fmtDate(row.next_run_time) : "—"
            }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_paused ? 'info' : 'success'" size="small">
              {{ row.is_paused ? "已暂停" : "运行中" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="description"
          label="说明"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="permStore.hasPermission('system.jobs.trigger')"
              size="small"
              type="primary"
              plain
              :loading="triggeringId === row.id"
              @click="handleTrigger(row)"
            >
              立即触发
            </el-button>
            <el-button
              v-if="
                permStore.hasPermission('system.jobs.manage') &&
                !row.is_paused &&
                row.next_run_time !== null
              "
              size="small"
              type="warning"
              plain
              @click="handlePause(row)"
            >
              暂停
            </el-button>
            <el-button
              v-if="
                permStore.hasPermission('system.jobs.manage') && row.is_paused
              "
              size="small"
              type="success"
              plain
              @click="handleResume(row)"
            >
              恢复
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Refresh } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { onMounted, ref } from "vue";

import { type JobPublic, jobsApi } from "@/api/jobs";
import { usePermissionStore } from "@/stores/permission";

const permStore = usePermissionStore();

const loading = ref(false);
const jobs = ref<JobPublic[]>([]);
const triggeringId = ref<string | null>(null);

async function loadJobs() {
  loading.value = true;
  try {
    const res = await jobsApi.list();
    jobs.value = res.data.data;
  } catch {
    ElMessage.error("加载任务列表失败");
  } finally {
    loading.value = false;
  }
}

async function handleTrigger(row: JobPublic) {
  triggeringId.value = row.id;
  try {
    const res = await jobsApi.trigger(row.id);
    ElMessage.success(res.data.message);
  } catch {
    ElMessage.error(`触发任务 "${row.name}" 失败`);
  } finally {
    triggeringId.value = null;
  }
}

async function handlePause(row: JobPublic) {
  try {
    const res = await jobsApi.pause(row.id);
    const idx = jobs.value.findIndex((j) => j.id === row.id);
    if (idx !== -1) jobs.value[idx] = res.data;
    ElMessage.success(`任务 "${row.name}" 已暂停`);
  } catch {
    ElMessage.error(`暂停任务 "${row.name}" 失败`);
  }
}

async function handleResume(row: JobPublic) {
  try {
    const res = await jobsApi.resume(row.id);
    const idx = jobs.value.findIndex((j) => j.id === row.id);
    if (idx !== -1) jobs.value[idx] = res.data;
    ElMessage.success(`任务 "${row.name}" 已恢复`);
  } catch {
    ElMessage.error(`恢复任务 "${row.name}" 失败`);
  }
}

function triggerTagType(trigger: string): "primary" | "success" | "warning" {
  if (trigger === "cron") return "primary";
  if (trigger === "interval") return "success";
  return "warning";
}

function fmtDate(val: string) {
  return new Date(val).toLocaleString("zh-CN", { hour12: false });
}

onMounted(loadJobs);
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
