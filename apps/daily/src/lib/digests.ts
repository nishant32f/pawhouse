export type {
  ReadEdition as Edition,
  ReadStory as Story,
  ReadActiveStory as ActiveStory,
  ReadArchivedStory as ArchivedStory,
} from "../../../../hermes/ai-x-digest/content/wire.ts"
import type { ReadEdition } from "../../../../hermes/ai-x-digest/content/wire.ts"
export type IdentifiedEdition = Extract<ReadEdition, { kind: "identified" }>
export type { Source } from "../../../../hermes/ai-x-digest/content/parser.ts"
