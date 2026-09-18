import { AxiosHeaders, type InternalAxiosRequestConfig } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * 请求层的 401 静默刷新测试。
 *
 * 规则: access token 过期(30 分钟)时, 用 refresh token 换一对新令牌并**重放原请求**,
 * 而不是直接把用户踢到登录页。这里用假 adapter 精确构造 401, 覆盖三个关键点:
 *   1. 刷新成功后原请求自动重放, 新令牌写回 localStorage
 *   2. 并发的多个 401 只刷新一次 —— 后端 refresh token 是一次性轮换的,
 *      并发刷新会让后到的那次拿到已失效的令牌, 整页掉线
 *   3. 刷新接口自身返回 401 时不能再次触发刷新(否则无限循环)
 */

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() },
}))

import request, { rawAxios, refreshClient } from './http'
import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY, getAccessToken, getRefreshToken } from '@/utils/tokenStorage'

const ok = (config: InternalAxiosRequestConfig, body: unknown) => ({
  data: body,
  status: 200,
  statusText: 'OK',
  headers: new AxiosHeaders(),
  config,
  request: {},
})

const unauthorized = (config: InternalAxiosRequestConfig) =>
  Promise.reject(
    Object.assign(new Error('Request failed with status code 401'), {
      config,
      isAxiosError: true,
      response: {
        data: { code: 401, message: '登录状态已过期' },
        status: 401,
        statusText: 'Unauthorized',
        headers: new AxiosHeaders(),
        config,
      },
    }),
  )

/** 刷新接口的固定成功响应: { code, message, data: TokenPair } */
const tokenPair = (access: string, refresh: string) => ({
  code: 0,
  message: 'ok',
  data: { access_token: access, refresh_token: refresh, token_type: 'bearer' },
})

function seedTokens(access = 'old-access', refresh = 'old-refresh') {
  localStorage.setItem(ACCESS_TOKEN_KEY, access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

/** 构造一个假 adapter: 前 failTimes 次对 targetUrl 返回 401, 之后成功 */
function fakeProtectedAdapter(targetUrl: string, failTimes: number) {
  const seen: string[] = []
  let hits = 0
  const adapter = async (config: InternalAxiosRequestConfig) => {
    if (config.url !== targetUrl) return unauthorized(config)
    seen.push(String(config.headers?.Authorization || ''))
    hits += 1
    if (hits <= failTimes) return unauthorized(config)
    return ok(config, { code: 0, message: 'ok', data: { id: 1, hit: hits } })
  }
  return { adapter, seen }
}

describe('api/http 的 401 静默刷新', () => {
  beforeEach(() => {
    localStorage.clear()
    location.hash = ''
  })

  it('access 过期时用 refresh token 换新令牌并重放原请求', async () => {
    seedTokens()
    const protectedApi = fakeProtectedAdapter('/posts/1', 1)
    rawAxios.defaults.adapter = protectedApi.adapter

    let refreshCalls = 0
    refreshClient.defaults.adapter = async (config) => {
      refreshCalls += 1
      expect(config.url).toBe('/auth/refresh')
      // 刷新请求必须带上当前 refresh token
      expect(JSON.parse(String(config.data))).toEqual({ refresh_token: 'old-refresh' })
      return ok(config, tokenPair('new-access', 'new-refresh'))
    }

    const data = await request.get('/posts/1')

    expect(data).toEqual({ id: 1, hit: 2 })
    expect(refreshCalls).toBe(1)
    expect(getAccessToken()).toBe('new-access')
    expect(getRefreshToken()).toBe('new-refresh')
    // 第二次请求(重放)必须用新令牌
    expect(protectedApi.seen[1]).toBe('Bearer new-access')
  })

  it('并发的多个 401 只触发一次刷新(单飞)', async () => {
    seedTokens()
    const first = fakeProtectedAdapter('/posts/1', 1)
    const second = fakeProtectedAdapter('/posts/2', 1)
    const adapters = new Map([
      ['/posts/1', first.adapter],
      ['/posts/2', second.adapter],
    ])
    rawAxios.defaults.adapter = (config) => {
      const adapter = adapters.get(String(config.url))
      return adapter ? adapter(config) : unauthorized(config)
    }

    let refreshCalls = 0
    let releaseRefresh: (() => void) | undefined
    refreshClient.defaults.adapter = (config) => {
      refreshCalls += 1
      return new Promise((resolve) => {
        releaseRefresh = () => resolve(ok(config, tokenPair('new-access', 'new-refresh')))
      })
    }

    const pending = [request.get('/posts/1'), request.get('/posts/2')]
    // 等两个请求都走到 401; 刷新 Promise 是模块级的, 必须让它有机会结算,
    // 否则挂在下面的 finally 里释放不掉, 会污染后续用例。
    try {
      await vi.waitFor(() => expect(refreshCalls).toBe(1))
    } finally {
      releaseRefresh?.()
    }

    await expect(Promise.all(pending)).resolves.toEqual([
      { id: 1, hit: 2 },
      { id: 1, hit: 2 },
    ])
    expect(refreshCalls).toBe(1)
  })

  it('重放后仍然 401 时不会无限重试', async () => {
    seedTokens()
    const always401 = fakeProtectedAdapter('/posts/1', Number.POSITIVE_INFINITY)
    rawAxios.defaults.adapter = always401.adapter

    let refreshCalls = 0
    refreshClient.defaults.adapter = async (config) => {
      refreshCalls += 1
      return ok(config, tokenPair('new-access', 'new-refresh'))
    }

    await expect(request.get('/posts/1')).rejects.toBeTruthy()

    // 只重放一次: 原始请求 + 一次重放
    expect(always401.seen).toHaveLength(2)
    expect(refreshCalls).toBe(1)
  })

  it('刷新令牌也失效时清空登录态并跳登录页', async () => {
    seedTokens()
    location.hash = '#/write'
    rawAxios.defaults.adapter = (config) => unauthorized(config)
    // 刷新接口返回 401 -> 刷新失败
    refreshClient.defaults.adapter = (config) => unauthorized(config)

    await expect(request.get('/posts/1')).rejects.toBeTruthy()

    expect(getAccessToken()).toBe('')
    expect(getRefreshToken()).toBe('')
    expect(location.hash).toBe('#/admin/login')
  })

  it('刷新接口自身的 401 不再触发刷新(防循环)', async () => {
    seedTokens()
    let adapterHits = 0
    rawAxios.defaults.adapter = (config) => {
      adapterHits += 1
      return unauthorized(config)
    }
    let refreshCalls = 0
    refreshClient.defaults.adapter = async (config) => {
      refreshCalls += 1
      return unauthorized(config)
    }

    await expect(request.post('/auth/refresh', { refresh_token: 'old-refresh' })).rejects.toBeTruthy()

    expect(refreshCalls).toBe(0)
    expect(adapterHits).toBe(1)
    expect(getAccessToken()).toBe('')
  })

  it('没有 refresh token 时不尝试刷新, 直接按未登录处理', async () => {
    localStorage.setItem(ACCESS_TOKEN_KEY, 'old-access') // 只有 access, 没有 refresh
    rawAxios.defaults.adapter = (config) => unauthorized(config)
    let refreshCalls = 0
    refreshClient.defaults.adapter = async (config) => {
      refreshCalls += 1
      return unauthorized(config)
    }

    await expect(request.get('/posts/1')).rejects.toBeTruthy()

    expect(refreshCalls).toBe(0)
    expect(getAccessToken()).toBe('')
  })

  it('非 401 错误不触发刷新', async () => {
    seedTokens()
    rawAxios.defaults.adapter = (config) =>
      Promise.reject(
        Object.assign(new Error('boom'), {
          config,
          isAxiosError: true,
          response: {
            data: { code: 500, message: '服务器内部错误' },
            status: 500,
            statusText: 'Server Error',
            headers: new AxiosHeaders(),
            config,
          },
        }),
      )
    let refreshCalls = 0
    refreshClient.defaults.adapter = async (config) => {
      refreshCalls += 1
      return unauthorized(config)
    }

    await expect(request.get('/posts/1')).rejects.toBeTruthy()

    expect(refreshCalls).toBe(0)
    // 500 不应该把用户踢下线
    expect(getAccessToken()).toBe('old-access')
  })
})
