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

const sessions = ref<Session[]>([]);
const sessionId = ref<string | null>(null);
const messages = ref<ChatMessage[]>([]);
const input = ref("");
const busy = ref(false);
const error = ref("");
const pending = ref(false);
const scroller = ref<HTMLElement | null>(null);
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
  <section class="hero">
    <div class="eyebrow">LET’S TALK ABOUT YOUR NEXT STOP.</div>
    <h1>从一个想法聊起。</h1>
    <p class="muted">问景点、天气或路线。对话会保存，随时回来继续。</p>
  </section>
  <div class="chat-layout">
    <aside class="panel">
      <a-button block :disabled="busy" @click="newSession"
        >＋ 新建对话</a-button
      >
      <p class="muted">最近的对话</p>
      <button
        v-for="session in sessions"
        :key="session.id"
        class="session"
        :class="{ active: sessionId === session.id }"
        :disabled="busy"
        @click="select(session.id)"
      >
        {{ session.title }}
      </button>
    </aside>
    <section class="panel">
      <div ref="scroller" class="chat-history" aria-live="polite">
        <p v-if="!messages.length" class="muted">
          例如：帮我找找杭州适合散步的地方。
        </p>
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="bubble"
          :class="message.role"
        >
          <strong>{{ message.role === "human" ? "你" : "途间" }}</strong>
          <div>{{ message.content }}</div>
        </div>
        <p v-if="busy" class="muted">正在处理，可能需要查询地图工具…</p>
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
      <form @submit.prevent="send(false)">
        <label class="field"
          ><span>消息</span
          ><textarea
            v-model="input"
            rows="3"
            maxlength="4000"
            placeholder="说说你的旅行想法…"
            :disabled="busy || pending"
          ></textarea>
        </label>
        <div class="actions">
          <a-button
            type="primary"
            html-type="submit"
            :loading="busy"
            :disabled="pending || !input.trim()"
            >发送</a-button
          ><RouterLink to="/">想安排完整行程？打开规划表单 →</RouterLink>
        </div>
      </form>
    </section>
  </div>
</template>
