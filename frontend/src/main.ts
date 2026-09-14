import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import { Button, ConfigProvider } from "ant-design-vue";
import "ant-design-vue/dist/reset.css";
import "./style.css";
import App from "./App.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: () => import("./views/Home.vue") },
    { path: "/result", component: () => import("./views/Result.vue") },
    { path: "/chat", component: () => import("./views/Chat.vue") },
  ],
});
createApp(App).use(router).use(Button).use(ConfigProvider).mount("#app");
