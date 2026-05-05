<template>
  <div class="welcome">
    <el-card>
      <template #header>欢迎使用企业管理后台</template>
      <p>
        您好，<strong>{{
          authStore.user?.nickname ?? authStore.user?.username
        }}</strong
        >！
      </p>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">{{
          authStore.user?.username
        }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{
          authStore.user?.email ?? "未设置"
        }}</el-descriptions-item>
        <el-descriptions-item label="超级管理员">
          <el-tag :type="authStore.user?.is_superuser ? 'danger' : 'info'">
            {{ authStore.user?.is_superuser ? "是" : "否" }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="账号状态">
          <el-tag :type="authStore.user?.is_active ? 'success' : 'warning'">
            {{ authStore.user?.is_active ? "正常" : "禁用" }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
const authStore = useAuthStore();
</script>

<style scoped>
.welcome {
  max-width: 800px;
}
</style>
