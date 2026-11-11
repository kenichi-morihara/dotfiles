// Dark Modern Rose: TypeScript showcase.
import { readFile } from "node:fs/promises";

export const RETRY_LIMIT = 3;

export type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };

export interface Repository<T> {
  find(id: string): Promise<T | null>;
}

function decorate(target: unknown, key: string) {}

export abstract class BaseService<T> implements Repository<T> {
  protected abstract table: string;

  @decorate
  async find(id: string): Promise<T | null> {
    for (let attempt = 1; attempt <= RETRY_LIMIT; attempt++) {
      try {
        const raw = await readFile(`${this.table}/${id}.json`, "utf8");
        return JSON.parse(raw) as T;
      } catch (error: unknown) {
        if (error instanceof SyntaxError) throw error;
      }
    }
    return null;
  }
}

export const isPresent = <T,>(value: T | null | undefined): value is T => value != null;
const pattern = /^[a-z]+\d*$/i;
const keys = Object.keys({ a: 1, b: 2 }) satisfies string[];
