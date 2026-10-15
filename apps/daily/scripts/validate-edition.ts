import { readFile } from "node:fs/promises"
import { basename } from "node:path"
import { parseEdition } from "../src/lib/digests"

const filename = process.argv[2]
if (!filename) throw new Error("Pass the privately staged Markdown edition path")
parseEdition({ filename: basename(filename), text: await readFile(filename, "utf8") })
