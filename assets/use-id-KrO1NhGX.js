import{En as e,Ji as t,_n as n,ni as r,oi as i,qt as a,vn as o}from"./api-0gbVCebA.js";var s={prefix:Math.floor(Math.random()*1e4),current:0},c=Symbol(`elIdInjection`),l=()=>r()?i(c,s):s,u=r=>{let i=l();!o&&i===s&&e(`IdInjection`,`Looks like you are using server rendering, you must provide a id provider to ensure the hydration process to be succeed
usage: app.provide(ID_INJECTION_KEY, {
  prefix: number,
  current: number,
})`);let c=a();return n(()=>t(r)||`${c.value}-id-${i.prefix}-${i.current++}`)};export{l as n,u as t};