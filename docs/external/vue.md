# Vue 3 + Vite — Implementation Reference

Source: https://vuejs.org/guide/quick-start.html,
https://vuejs.org/guide/essentials/reactivity-fundamentals.html,
https://router.vuejs.org/guide/

## Scaffolding a new project

```bash
npm create vue@latest
```

Interactive prompts offer: TypeScript, JSX, Vue Router, Pinia, Vitest,
E2E testing, ESLint, Prettier. For a small multi-step interview SPA, pick at
least **Vue Router** (needed for topic → questions → summary navigation);
Pinia/TypeScript/testing are optional extras.

```bash
cd <project-name>
npm install
npm run dev      # starts Vite dev server, default http://localhost:5173
npm run build    # production build to ./dist
```

Requires Node.js `^22.18.0 || >=24.12.0` (or use a recent LTS).

## Basic component structure (Composition API + `<script setup>`)

```vue
<!-- src/components/TopicForm.vue -->
<script setup>
import { ref } from 'vue'

const topic = ref('')
const emit = defineEmits(['submit'])

function handleSubmit() {
  if (topic.value.trim()) {
    emit('submit', topic.value)
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <input v-model="topic" placeholder="Enter a topic" />
    <button type="submit">Start Interview</button>
  </form>
</template>
```

`<script setup>` is the recommended, terser way to write Composition API
components — top-level bindings are automatically exposed to the template.

## Reactive state: `ref()` vs `reactive()`

```vue
<script setup>
import { ref, reactive } from 'vue'

const count = ref(0)              // primitives: access/mutate via .value
function increment() { count.value++ }

const state = reactive({ count: 0 })  // objects: mutate properties directly
</script>

<template>
  <button @click="increment">{{ count }}</button>       <!-- auto-unwrapped -->
  <button @click="state.count++">{{ state.count }}</button>
</template>
```

- Use `ref()` for primitives and as the default choice.
- Use `reactive()` for grouped object state; it cannot be reassigned wholesale
  and doesn't destructure reactively (destructured properties lose reactivity).
- In `<script>`, refs need `.value`; templates unwrap refs automatically.

## Calling a backend API from a component

Using `fetch` (no extra dependency):

```vue
<script setup>
import { ref } from 'vue'

const questions = ref([])
const loading = ref(false)

async function startInterview(topic) {
  loading.value = true
  try {
    const res = await fetch('http://localhost:8000/interviews/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic }),
    })
    if (!res.ok) throw new Error(`API error: ${res.status}`)
    questions.value = await res.json()
  } finally {
    loading.value = false
  }
}
</script>
```

Using `axios` (if added via `npm install axios`):

```js
import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000' })

const { data } = await api.post('/interviews/', { topic })
```

Remember: the FastAPI backend must enable CORS for the Vite dev origin
(`http://localhost:5173`) — see `docs/external/fastapi.md`.

## Routing for a multi-step interview flow

```bash
npm install vue-router@4   # if not selected during scaffold
```

```js
// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import TopicView from '../views/TopicView.vue'
import QuestionsView from '../views/QuestionsView.vue'
import SummaryView from '../views/SummaryView.vue'

const routes = [
  { path: '/', component: TopicView },
  { path: '/interview/:id/questions', component: QuestionsView, props: true },
  { path: '/interview/:id/summary', component: SummaryView, props: true },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
```

```js
// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'

createApp(App).use(router).mount('#app')
```

```vue
<!-- App.vue -->
<template>
  <router-view />
</template>
```

Programmatic navigation between steps (e.g. after submitting the topic form):

```js
import { useRouter } from 'vue-router'
const router = useRouter()

async function onTopicSubmit(topic) {
  const interview = await startInterview(topic)
  router.push(`/interview/${interview.id}/questions`)
}
```

`useRoute()` reads the current route's params (e.g. `:id`) inside a
component; `router.push(path)` navigates without a full page reload.
