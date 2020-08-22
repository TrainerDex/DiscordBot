from danger_python import Danger, markdown

danger = Danger()
title = danger.github.pr.title
markdown(title)
