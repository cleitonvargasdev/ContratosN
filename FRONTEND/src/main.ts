import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import './assets/styles.css'
import 'sweetalert2/dist/sweetalert2.min.css'

createApp(App).use(router).mount('#app')

