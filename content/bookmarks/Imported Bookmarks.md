---
layout: default
title: Bookmarks
permalink: /bookmarks/
---

<div class="archive">

{% assign bookmarks_by_month = site.bookmarks | reverse | group_by_exp: "b", "b.date | date: '%B %Y'" %}

{% if bookmarks_by_month.size == 0 %}
<p>No bookmarks yet. Share a link with pawalker on Telegram to add one.</p>
{% endif %}

{% for month in bookmarks_by_month %}
<h2>{{ month.name }}</h2>
<ul>
{% for bm in month.items %}
<li><a href="{{ bm.url | relative_url }}">{{ bm.title }}</a>{% if bm.source_url %} (<a href="{{ bm.source_url }}">source</a>){% endif %} <small>{{ bm.date | date: "%b %d" }}</small></li>
{% endfor %}
</ul>
{% endfor %}

</div>
