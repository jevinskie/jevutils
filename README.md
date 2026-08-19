# jevutils
Various utilities I wrote for my use. My favorite so far is a find(1) alternative that searches using libmagic

# one-liners
## find python files and sort by modification time
`fd -e py -t f -0 | xargs -0 ls -lt`
