# Swim Info

### App designed to collect swim statistics for announcers at swim meets, consisting of a web scraper and interface built with Python and Beautiful Soup. It processes start lists and scrapes online meet results to provide splits for each swimmer’s best time.

Add the LiveTiming session program url to `main.py` and run the script. It will then scrape [Tempus Open](https://www.tempusopen.se/index.php?r=Swimmer) and [LiveTiming](https://www.livetiming.se/) meet archives to generate `session_data.json` with splits for each swimmer’s best time. Then, `index.html` will be generated with a UI to view the data.

![Image of the UI](/ui-image.jpg)

#### By [Marcus Alenius](https://www.linkedin.com/in/marcusalenius/)