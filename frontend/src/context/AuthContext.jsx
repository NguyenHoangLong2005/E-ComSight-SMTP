import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const saved = localStorage.getItem('user')
    if (token && saved) {
      try {
        setUser(JSON.parse(saved))
      } catch {}
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    const res = await authAPI.login(username, password)
    const { access_token, ...userInfo } = res.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(userInfo))
    setUser(userInfo)
    return userInfo
  }

  const register = async (data) => {
    const res = await authAPI.register(data)
    const { access_token, ...userInfo } = res.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(userInfo))
    setUser(userInfo)
    return userInfo
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  const updateUser = (data) => {
    const updated = { ...user, ...data }
    localStorage.setItem('user', JSON.stringify(updated))
    setUser(updated)
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout, updateUser, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
