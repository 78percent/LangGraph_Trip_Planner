<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, RouterView } from "vue-router";
import { checkBackend, errorMessage } from "@/services/api";
import AppIcon from "@/components/AppIcon.vue";

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
        colorPrimary: '#285448',
        borderRadius: 12,
        controlHeight: 44,
        fontFamily: 'inherit',
      },
    }"
  >
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <header class="site-header">
      <RouterLink to="/" class="brand" aria-label="途间首页">
        <span class="brand-mark"><AppIcon name="compass" :size="27" /></span>
        <span class="brand-name"
          >途间<span class="brand-english">T U J I A N</span></span
        >
      </RouterLink>
      <nav aria-label="主要导航">
        <RouterLink to="/"
          ><AppIcon name="compass" :size="17" />规划旅行</RouterLink
        >
        <RouterLink to="/chat"
          ><AppIcon name="chat" :size="17" />旅行对话</RouterLink
        >
      </nav>
    </header>
    <main id="main-content" class="page" tabindex="-1">
      <div v-if="backendError" role="alert" class="error">
        {{ backendError }}
        <a-button size="small" :loading="checking" @click="verifyBackend"
          >重新检查连接</a-button
        >
      </div>
      <RouterView />
    </main>
    <footer class="site-footer">
      <span class="footer-brand">途间 <span>·</span> 把日子过成旅途</span>
    </footer>
  </a-config-provider>
</template>
