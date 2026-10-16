/** Decode frozen prose with the content package, without importing reader views. */
import { readFileSync } from "node:fs"
import {
  decodeEdition,
  materializeEdition,
  type ReadStory,
} from "../hermes/ai-x-digest/content/wire.ts"
import { pointValue } from "../hermes/ai-x-digest/content/format.ts"

function proofStory(story: ReadStory) {
  const visual = story.editorial?.visual
  return { ...story, proofPointValues: visual?.kind === "bar" ? visual.points.map(pointValue) : [] }
}
process.stdout.write(
  JSON.stringify(
    process.argv.slice(2).map((filename) => {
      const edition = materializeEdition(decodeEdition(JSON.parse(readFileSync(filename, "utf8"))))
      return edition.kind === "legacy"
        ? edition
        : {
            ...edition,
            stories: edition.stories.map(proofStory),
            activeStories: edition.activeStories.map(proofStory),
            archivedStories: edition.archivedStories.map(proofStory),
          }
    }),
  ),
)
