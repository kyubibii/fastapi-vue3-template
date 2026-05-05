<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <el-button text @click="router.back()">← 返回</el-button>
          <span>{{ isEdit ? "编辑用户" : "新建用户" }}</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        style="max-width: 500px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item
          :label="isEdit ? '新密码' : '密码'"
          :prop="isEdit ? '' : 'password'"
        >
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="isEdit ? '不填则不修改' : '请输入密码'"
          />
        </el-form-item>
        <el-form-item label="账号状态">
          <el-switch
            v-model="form.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
        <el-form-item label="超级管理员">
          <el-switch v-model="form.is_superuser" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSubmit"
            >保存</el-button
          >
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import { usersApi } from "@/api/users";

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const formRef = ref<FormInstance>();
const saving = ref(false);
const form = reactive({
  username: "",
  nickname: "",
  email: "",
  password: "",
  is_active: true,
  is_superuser: false,
});

const rules: FormRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  nickname: [{ required: true, message: "请输入昵称", trigger: "blur" }],
  password: [
    { required: true, min: 8, message: "密码至少8位", trigger: "blur" },
  ],
};

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) return;
  saving.value = true;
  try {
    if (isEdit.value) {
      const payload: Record<string, unknown> = {
        nickname: form.nickname,
        email: form.email || undefined,
        is_active: form.is_active,
        is_superuser: form.is_superuser,
      };
      if (form.password) payload.password = form.password;
      await usersApi.update(route.params.id as string, payload);
      ElMessage.success("更新成功");
    } else {
      await usersApi.create({
        username: form.username,
        nickname: form.nickname,
        password: form.password,
        email: form.email || undefined,
        is_active: form.is_active,
        is_superuser: form.is_superuser,
      });
      ElMessage.success("创建成功");
    }
    router.push("/users");
  } catch {
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  if (isEdit.value) {
    try {
      const res = await usersApi.get(route.params.id as string);
      Object.assign(form, {
        username: res.data.username,
        nickname: res.data.nickname,
        email: res.data.email ?? "",
        is_active: res.data.is_active,
        is_superuser: res.data.is_superuser,
      });
    } catch {
      ElMessage.error("加载用户信息失败");
      router.back();
    }
  }
});
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
