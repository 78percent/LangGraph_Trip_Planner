<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, RouterView } from "vue-router";
import { checkBackend, errorMessage } from "@/services/api";

const backendError = ref("");
const checking = ref(false);
async function verifyBackend() {
  checking.value = true;
  try {
    await checkBackend();
    backendError.value = "";
  } catch (error) {
    backendError.value = errorMessage(error);
  } finally {
    checking.value = false;
  }
}
onMounted(verifyBackend);
</script>

<template>
  <a-config-provider
    :theme="{
      token: {
        colorPrimary: '#286557',
        borderRadius: 10,
        fontFamily: 'inherit',
      },
    }"
  >
    <header class="site-header">
      <RouterLink to="/" class="brand"
        >途间<span>TRAVEL, THOUGHTFULLY.</span></RouterLink
      >
      <nav>
        <RouterLink to="/">规划旅行</RouterLink
        ><RouterLink to="/chat">旅行对话</RouterLink>
      </nav>
    </header>
    <main class="page">
      <div v-if="backendError" role="alert" class="error">
        {{ backendError }}
        <a-button size="small" :loading="checking" @click="verifyBackend">重新检查连接</a-button>
      </div>
      <RouterView />
    </main>
    <footer>
      把想去的地方，变成可出发的计划。<span
        >真实地点 · 清楚的估算 · 自己的节奏</span
      >
    </footer>
  </a-config-provider>
</template>
