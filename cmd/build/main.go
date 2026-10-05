package main

import (
	"html"
	"log"
	"os"
	"strings"

	"github.com/x1ah/gena"
	"github.com/x1ah/gena/generators"
)

func main() {
	cfg, err := gena.ParseConfig(".build/config.yml")
	if err != nil {
		log.Fatal(err)
	}
	if cfg.Template != "webstack" {
		log.Fatal("Only the webstack theme is supported")
	}
	// The upstream theme uses text/template; escape user-authored text and URLs.
	cfg.Title = html.EscapeString(cfg.Title)
	cfg.Description = html.EscapeString(cfg.Description)
	cfg.Footer = html.EscapeString(cfg.Footer)
	cfg.URL = html.EscapeString(cfg.URL)
	cfg.Github = html.EscapeString(cfg.Github)
	cfg.Favicon = html.EscapeString(cfg.Favicon)
	for _, category := range cfg.Content.Categories {
		category.Name = html.EscapeString(category.Name)
		for _, site := range category.Sites {
			site.Name = html.EscapeString(site.Name)
			site.Description = html.EscapeString(site.Description)
			// URLs also appear inside single-quoted inline JavaScript in WebStack.
			site.URL = html.EscapeString(strings.NewReplacer("'", "%27", "\\", "%5C").Replace(site.URL))
			site.Icon = html.EscapeString(site.Icon)
		}
	}
	file, err := os.Create(".build/index.html")
	if err != nil {
		log.Fatal(err)
	}
	(&generators.WebStackGenerator{}).Run(cfg, file)
	if err := file.Close(); err != nil {
		log.Fatal(err)
	}
	if err := os.Rename(".build/index.html", "index.html"); err != nil {
		log.Fatal(err)
	}
}
