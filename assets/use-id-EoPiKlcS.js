import{Wt as e,ei as t,gn as n,hn as r,ii as i,qi as a,wn as o}from"./api-BMxcx3XB.js";var s={prefix:Math.floor(Math.random()*1e4),current:0},c=Symbol(`elIdInjection`),l=()=>t()?i(c,s):s,u=t=>{let i=l();!n&&i===s&&o(`IdInjection`,`Looks like you are using server rendering, you must provide a id provider to ensure the hydration process to be succeed
usage: app.provide(ID_INJECTION_KEY, {
  prefix: number,
  current: number,
})`);let c=e();return r(()=>a(t)||`${c.value}-id-${i.prefix}-${i.current++}`)};export{l as n,u as t};