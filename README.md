# docsthebox

![screenshot of notion database](.img/notebook.png)

## whats this?

docsthebox hits the hack the box api and gets all api data on the machines.

machines are stored in specified the notion database if they don't exist yet.

each page has basic templates attached to help document your exploitation.

## how do i use this?

glad you asked -- please check out the [usage instructions](USAGE.md).

you *will* need to set some things up so please read it.

easiest is to run the docker container if you have docker, otherwise run the python code.

sorry windows users, you might have to changes some paths. or just run the docker container.

## what else is needed?

maybe use notionx library over raw json + requests

code cleanup and commenting

## known bugs

hack the box has an incredibly aggresive cloudflare configuration and notion can
sometimes not fetch the images from hack the box without receiving a 403 denied.
this may cause images to not load sometimes. sorry, blame htb for their CF config.

## creds

- [ritchies](https://github.com/ritchies)

- [goproslowyo](https://github.com/goproslowyo)

- thomas frank for inspiration

![screenshot of notion notebook page](.img/page1.png)
![another screenshot of notion notebook page](.img/page2.png)
