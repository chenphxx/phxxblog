import{Jt as e,On as t,Zi as n,bn as r,ci as i,ii as a,yn as o}from"./api-BTjDRI45.js";var s={prefix:Math.floor(Math.random()*1e4),current:0},c=Symbol(`elIdInjection`),l=()=>a()?i(c,s):s,u=i=>{let a=l();!r&&a===s&&t(`IdInjection`,`Looks like you are using server rendering, you must provide a id provider to ensure the hydration process to be succeed
usage: app.provide(ID_INJECTION_KEY, {
  prefix: number,
  current: number,
})`);let c=e();return o(()=>n(i)||`${c.value}-id-${a.prefix}-${a.current++}`)};export{l as n,u as t};