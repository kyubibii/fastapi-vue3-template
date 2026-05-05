<template>
  <div class="forbidden">
    <el-result
      icon="warning"
      title="403 无访问权限"
      sub-title="您没有权限访问该页面，请联系管理员。"
    >
      <template #extra>
        <el-button type="primary" @click="router.push('/dashboard')"
          >返回首页</el-button
        >
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
const router = useRouter();
</script>

<style scoped>
.forbidden {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}
</style>
