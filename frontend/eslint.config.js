// ESLint 扁平配置: 只管"能自动拦截的错误", 格式交给 Prettier(eslint-config-prettier 关闭冲突规则)。
// 类型检查由 vue-tsc 负责, 这里不启用 typescript-eslint 的类型感知规则(那需要 project 配置, 会明显变慢)。
import js from '@eslint/js'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import pluginVue from 'eslint-plugin-vue'
import prettier from 'eslint-config-prettier'

export default [
  {
    ignores: [
      'dist/**',
      'coverage/**',
      // 由 unplugin-vue-components 生成
      'src/components.d.ts',
      // 主题子系统的生成物(生成器自己写出来的, 格式由生成器决定)
      'src/styles/themes/*.css',
      'src/styles/themes/registry.ts',
      'public/**',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: { parser: tseslint.parser },
    },
  },
  {
    files: ['src/**/*.{ts,vue}'],
    languageOptions: {
      globals: { ...globals.browser },
    },
  },
  {
    // 看板娘的形象名是专有名词, 不适用"组件名必须是多个单词"的约定
    files: ['src/components/Kanbanniang.vue'],
    rules: { 'vue/multi-word-component-names': 'off' },
  },
  {
    files: ['scripts/**/*.mjs', 'src/styles/themes/_source/**/*.mjs', '*.{ts,mjs}'],
    languageOptions: {
      globals: { ...globals.node },
    },
  },
  prettier,
]
