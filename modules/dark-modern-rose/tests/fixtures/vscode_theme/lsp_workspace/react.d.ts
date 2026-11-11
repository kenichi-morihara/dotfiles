// Minimal stand-in for @types/react so the fixture type-checks without node_modules.
declare module "react" {
  export function useState<T>(initial: T): [T, (value: T) => void];
}
declare namespace JSX {
  interface Element {}
  interface IntrinsicElements { [name: string]: any }
  interface IntrinsicAttributes { key?: unknown }
}
