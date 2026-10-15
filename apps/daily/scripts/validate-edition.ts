import { readFile } from "node:fs/promises"
import { basename } from "node:path"
import { parseEdition } from "../src/lib/digests"

const filename = process.argv[2]
if (!filename) throw new Error("Pass the privately staged Markdown edition path")
const edition = parseEdition({
  filename: basename(filename),
  text: await readFile(filename, "utf8"),
})
const previousFilename = process.argv[3]
if (previousFilename) {
  const previous = parseEdition({
    filename: basename(previousFilename),
    text: await readFile(previousFilename, "utf8"),
  })
  if (previous.kind === "identified" && edition.kind === "identified") {
    for (const archived of edition.archivedStories) {
      const original = previous.stories.find((story) => story.id === archived.id)
      if (original && JSON.stringify(archived.sources) !== JSON.stringify(original.sources)) {
        throw new Error(`${archived.id}: archived sources must match the previous revision`)
      }
    }
  }
}
