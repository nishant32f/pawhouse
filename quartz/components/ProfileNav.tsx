import { joinSegments, pathToRoot } from "../util/path"
import { QuartzComponentConstructor, QuartzComponentProps } from "./types"

type ProfileNavProps = Pick<QuartzComponentProps, "fileData"> & {
  cfg: Pick<QuartzComponentProps["cfg"], "baseUrl">
}

function ProfileNav({ fileData, cfg }: ProfileNavProps) {
  const baseDir =
    fileData.slug === "404"
      ? new URL(`https://${cfg.baseUrl ?? "example.com"}`).pathname
      : fileData.slug
        ? pathToRoot(fileData.slug)
        : "."
  return (
    <nav class="profile-nav" aria-label="Site">
      <a
        class="internal"
        data-no-popover="true"
        href={joinSegments(baseDir, "about")}
        aria-current={fileData.slug === "about" ? "page" : undefined}
      >
        About
      </a>
      <a
        class="internal"
        data-no-popover="true"
        href={baseDir.endsWith("/") ? baseDir : joinSegments(baseDir, "/")}
        aria-current={fileData.slug === "index" ? "page" : undefined}
      >
        Garden
      </a>
    </nav>
  )
}

ProfileNav.css = `
.profile-nav { display: flex; gap: 1.5rem; font-family: var(--codeFont); font-size: 0.9rem; }
.profile-nav a.internal { padding: 0.35rem 0; background: transparent; }
.profile-nav a.internal[aria-current="page"] { color: var(--dark); text-decoration: underline; }
.profile-nav a.internal:focus-visible { outline: 2px solid var(--secondary); outline-offset: 4px; }
`

export default (() => ProfileNav) satisfies QuartzComponentConstructor
