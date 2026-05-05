<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <el-button text @click="router.back()">← 返回</el-button>
          <span>{{ isEdit ? "编辑物品" : "新建物品" }}</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
        style="max-width: 500px"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="4" />
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
import { itemsApi } from "@/api/items";

const route = useRoute();
const router = useRouter();
const isEdit = computed(() => !!route.params.id);
const formRef = ref<FormInstance>();
const saving = ref(false);
const form = reactive({ title: "", description: "" });

const rules: FormRules = {
  title: [{ required: true, message: "请输入标题", trigger: "blur" }],
};

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) return;
  saving.value = true;
  try {
    if (isEdit.value) {
      await itemsApi.update(route.params.id as string, form);
      ElMessage.success("更新成功");
    } else {
      await itemsApi.create(form);
      ElMessage.success("创建成功");
    }
    router.push("/items");
  } catch {
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  if (isEdit.value) {
    try {
      const res = await itemsApi.get(route.params.id as string);
      form.title = res.data.title;
      form.description = res.data.description ?? "";
    } catch {
      ElMessage.error("加载物品信息失败");
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
