<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";
import {
  errorMessage,
  getHistory,
  listSessions,
  resumeSession,
  sendMessage,
} from "@/services/api";
import type { ChatMessage, Session } from "@/types";
import AppIcon from "@/components/AppIcon.vue";

const sessions = ref<Session[]>([]);
const sessionId = ref<string | null>(null);
const messages = ref<ChatMessage[]>([]);
const input = ref("");
const busy = ref(false);
const error = ref("");
const pending = ref(false);
const scroller = ref<HTMLElement | null>(null);
const composer = ref<HTMLTextAreaElement | null>(null);
function usePrompt(text: string) {
  input.value = text;
  composer.value?.focus();
}
async function refreshSessions() {
  sessions.value = await listSessions();
}
onMounted(async () => {
  try {
    await refreshSessions();
  } catch (e) {
    error.value = errorMessage(e);
  }
});
function newSession() {
  if (busy.value) return;
  sessionId.value = null;
  messages.value = [];
  error.value = "";
  pending.value = false;
}
async function select(id: string) {
  if (busy.value) return;
  busy.value = true;
  error.value = "";
  try {
    const data = await getHistory(id);
    sessionId.value = id;
    messages.value = data.messages;
    pending.value = data.pending;
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    busy.value = false;
  }
}
async function scroll() {
  await nextTick();
  if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight;
}
async function send(resume = false) {
  if (busy.value || (!resume && !input.value.trim())) return;
  busy.value = true;
  error.value = "";
  const text = input.value.trim();
  try {
    const result =
      resume && sessionId.value
        ? await resumeSession(sessionId.value)
        : await sendMessage(text, sessionId.value);
    sessionId.value = result.session_id;
    const history = await getHistory(result.session_id);
    messages.value = history.messages;
    pending.value = history.pending;
    if (!resume) input.value = "";
    await refreshSessions();
    await scroll();
  } catch (e) {
    error.value = errorMessage(e);
    // A failed turn may still have a checkpoint. Refresh the list so it can be resumed.
    try {
      await refreshSessions();
      if (sessionId.value)
        pending.value = (await getHistory(sessionId.value)).pending;
    } catch {
      /* Preserve the actionable original error. */
    }
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section class="hero chat-hero">
    <h1>从一个想法聊起。</h1>
    <p class="muted">关于远方的好奇，都可以在这里聊聊。</p>
  </section>
  <div class="chat-layout">
    <aside class="panel chat-sidebar" aria-label="对话记录">
      <a-button
        block
        class="new-chat-button"
        :disabled="busy"
        @click="newSession"
        ><AppIcon name="plus" :size="17" />新建对话</a-button
      >
      <h2 class="sidebar-heading">最近的对话</h2>
      <p v-if="!sessions.length && !error" class="sidebar-empty">
        聊过的风景，会留在这里。
      </p>
      <button
        v-for="session in sessions"
        :key="session.id"
        class="session"
        :class="{ active: sessionId === session.id }"
        :disabled="busy"
        :aria-current="sessionId === session.id ? 'true' : undefined"
        :title="session.title"
        @click="select(session.id)"
      >
        <AppIcon name="chat" :size="16" /><span>{{ session.title }}</span>
      </button>
    </aside>
    <section class="panel conversation-panel" aria-label="旅行对话">
      <div class="conversation-heading">
        <span class="assistant-mark"><AppIcon name="compass" :size="22" /></span
        ><strong>途间旅行助手</strong
        ><RouterLink to="/" class="chat-plan-link"
          >规划行程<AppIcon name="diagonal" :size="16"
        /></RouterLink>
      </div>
      <div
        ref="scroller"
        class="chat-history"
        role="log"
        aria-label="聊天消息"
        aria-live="polite"
        :aria-busy="busy"
      >
        <div v-if="!messages.length" class="chat-empty">
          <span class="chat-empty-icon"
            ><AppIcon name="compass" :size="37"
          /></span>
          <h2>想出发，就从一句话开始。</h2>
          <p>找一处风景，问一段路线，或聊聊你的旅行想法。</p>
          <div class="prompt-list">
            <button
              v-for="prompt in [
                '杭州有哪些适合散步的地方？',
                '周末去成都，有什么美食推荐？',
                '帮我安排一次轻松的家庭旅行',
              ]"
              :key="prompt"
              :disabled="busy || pending"
              @click="usePrompt(prompt)"
            >
              {{ prompt }}<AppIcon name="diagonal" :size="15" />
            </button>
          </div>
        </div>
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="bubble"
          :class="message.role"
        >
          <strong class="message-author">{{
            message.role === "human" ? "你" : "途间"
          }}</strong>
          <div>{{ message.content }}</div>
        </div>
        <p v-if="busy" class="chat-thinking" role="status">
          <span class="thinking-dot"></span>正在为你寻找答案…
        </p>
      </div>
      <div v-if="error" role="alert" class="error">{{ error }}</div>
      <div v-if="pending" class="notice">
        上一轮还没有完成。<a-button
          size="small"
          :loading="busy"
          @click="send(true)"
          >继续未完成会话</a-button
        >
      </div>
      <form class="chat-composer" @submit.prevent="send(false)">
        <label class="field"
          ><span class="sr-only">消息</span
          ><textarea
            ref="composer"
            v-model="input"
            rows="2"
            maxlength="4000"
            placeholder="说说你的旅行想法…"
            :disabled="busy || pending"
          ></textarea>
        </label>
        <div class="composer-actions">
          <a-button
            type="primary"
            html-type="submit"
            :loading="busy"
            :disabled="pending || !input.trim()"
            >发送<AppIcon name="send" :size="16"
          /></a-button>
        </div>
      </form>
    </section>
  </div>
</template>
