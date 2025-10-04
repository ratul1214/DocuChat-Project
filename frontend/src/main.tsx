import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './pages/App'
import './styles/index.css'
import AppRouter from "./AppRouter";

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>
)
