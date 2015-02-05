.PHONY: html

html:
	ipython nbconvert --to html *.ipynb
	mv *.html html