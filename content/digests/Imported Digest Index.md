---
layout: default
title: Archive
permalink: /digests/
---

<div class="archive">

{% assign digests_by_month = site.digests | reverse | group_by_exp: "d", "d.date | date: '%B %Y'" %}

{% for month in digests_by_month %}
<h2>{{ month.name }}</h2>
<ul>
{% for digest in month.items %}
<li><a href="{{ digest.url | relative_url }}">{{ digest.title }}</a> <small>{{ digest.date | date: "%b %d, %l:%M %p" }}</small></li>
{% endfor %}
</ul>
{% endfor %}

</div>
