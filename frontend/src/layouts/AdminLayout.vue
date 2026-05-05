<template>
  <el-container class="layout-container">
    <!-- Sidebar -->
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <span v-if="!isCollapsed" class="logo-text">企业管理后台</span>
        <el-icon v-else><Management /></el-icon>
      </div>

      <el-menu
        :default-active="activeMenuPath"
        :collapse="isCollapsed"
        router
        background-color="#1e293b"
        text-color="#94a3b8"
        active-text-color="#60a5fa"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>

        <template v-for="group in permStore.navigation" :key="group.id">
          <el-sub-menu :index="`group-${group.id}`">
            <template #title>
              <el-icon><Folder /></el-icon>
              <span>{{ group.name }}</span>
            </template>
            <el-menu-item
              v-for="page in group.pages"
              :key="page.id"
              :index="getPageMenuPath(page.page_url)"
              :disabled="!canNavigate(page.page_url)"
            >
              {{ page.name }}
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-aside>

    <!-- Main area -->
    <el-container>
      <!-- Header -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapsed = !isCollapsed">
            <Expand v-if="isCollapsed" />
            <Fold v-else />
          </el-icon>
        </div>
        <div class="header-right">
          <el-dropdown>
            <span class="user-info">
              <el-avatar
                size="small"
                :src="authStore.user?.avatar_url ?? undefined"
              />
              <span class="username">{{
                authStore.user?.nickname ?? authStore.user?.username
              }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout"
                  >退出登录</el-dropdown-item
                >
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- Content -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import {
  Management,
  HomeFilled,
  Folder,
  Expand,
  Fold,
  ArrowDown,
} from "@element-plus/icons-vue";
import { useAuthStore } from "@/stores/auth";
import { usePermissionStore } from "@/stores/permission";

const isCollapsed = ref(false);
const authStore = useAuthStore();
const permStore = usePermissionStore();
const router = useRouter();

function normalizeMenuPath(pageUrl: string | null): string | null {
  if (!pageUrl) return null;

  let normalized = pageUrl.trim();
  if (!normalized) return null;

  if (normalized === "/admin") return "/dashboard";
  if (normalized.startsWith("/admin/")) {
    normalized = normalized.slice("/admin".length);
  }
  if (!normalized.startsWith("/")) {
    normalized = `/${normalized}`;
  }

  return normalized;
}

function getPageMenuPath(pageUrl: string | null): string {
  return normalizeMenuPath(pageUrl) ?? "";
}

function canNavigate(pageUrl: string | null): boolean {
  return !!normalizeMenuPath(pageUrl);
}

const activeMenuPath = computed(() => {
  const currentPath = router.currentRoute.value.path;
  const menuPaths = permStore.navigation
    .flatMap((group) => group.pages)
    .map((page) => normalizeMenuPath(page.page_url))
    .filter((path): path is string => !!path);

  let matched = "";
  for (const path of menuPaths) {
    if (currentPath === path || currentPath.startsWith(`${path}/`)) {
      if (path.length > matched.length) matched = path;
    }
  }

  return matched || currentPath;
});

function handleLogout() {
  authStore.logout();
  permStore.clearNavigation();
  router.push("/login");
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #1e293b;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #f1f5f9;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #334155;
}

.logo-text {
  white-space: nowrap;
}

.el-menu {
  border-right: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 20px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #64748b;
}

.collapse-btn:hover {
  color: #3b82f6;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #475569;
}

.username {
  font-size: 14px;
}

.main-content {
  background: #f8fafc;
  padding: 20px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
