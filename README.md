# Women in Red Analytics Pipeline

** This is a work in progress**

## The Issue
The <a href="https://en.wikipedia.org/wiki/Wikipedia:WikiProject_Women_in_Red">Women in Red</a> WikiProject launched in 2015 to address the content gender gap on Wikipedia by adding more articles about women to the website. Thanks to efforts like Women in Red, the **percentage of articles about women on English Wikipedia increased from 15% in November 2014 to 17.91% in July 2019**. 

Some authors of Wikipedia articles about women have observed that articles about women seem more likely to get deleted from Wikipedia [1] [2].  Wikimedians who oversee gender equity projects report that Wikipedia's <a href="https://en.wikipedia.org/wiki/Wikipedia:Notability">Notability policy</a> is a major obstacle in closing the site's gender gap [3]. The policy requires that a subject has "significant coverage in reliable sources that are independent of the subject" in order to merit having a stand-alone Wiki page. 

**But significant women do not always have "significant" coverage in "respected" sources**. For example, when Donna Strickland won the Nobel Prize in October 2018, the physicist did not have a Wikipedia page [4]. Strickland's Wiki page was deleted in March 2018, when a volunteer editor asserted that Strickland did not meet the notability requirement because she did not have significant coverage in published sources [5].

How many other remarkable women are being denied stand alone Wikipedia pages because their accomplishments have not been celebrated in respected published sources? 

## Objectives
1. **Quantify the issue**: How many articles about women are deleted from Wikipedia? How often is the notability policy used to justify deleting an article about a woman?
2. **Explore the meaning of notability**: Compare how the notability policy is applied to Wikipedia articles about women and men. Are there meaningful differences in the types of secondary sources cited? How do editors explain why someone does not meet the notability criteria?

## Technical Approach
### AWS Data Processing Pipeline
![AWS pipeline](https://github.com/ozzysChiefDataScientist/women_in_red_pipeline/blob/master/pipeline_overview.png)

![Lambda Process 1: Download Daily AFD Log ](https://github.com/ozzysChiefDataScientist/women_in_red_pipeline/blob/master/download_daily_afd_log.png)

![Lambda Process 2: Extract Logs ](https://github.com/ozzysChiefDataScientist/women_in_red_pipeline/blob/master/extract_logs.png)

![Lambda Process 3: Download Individual AFD Page ](https://github.com/ozzysChiefDataScientist/women_in_red_pipeline/blob/master/download_indiv_afd_page.png)

![Lambda Process 4: Process Daily Pages ](https://github.com/ozzysChiefDataScientist/women_in_red_pipeline/blob/master/process_daily_pages.png)

### S3 Directory Structure

```
afd-scraped                         # — Root directory on S3
├── Articles_for_deletion/          #   SCRAPED DAILY SNAPSHOTS OF AFD MAIN PAGE
|                                   #   URL: https://en.wikipedia.org/wiki/Wikipedia:Articles_for_deletion
│   ├── {date}.txt                  #   The date the scraping was performed
|
├── daily_afd_analysis/             #   COMBINES individual_afd_analysis/ FILES INTO ONE MASTER FILE
│   ├── {date}.txt                  #   The date the scraping was performed
|
├── daily_afd_log/                  #   SCRAPED DAILY SNAPSHOTS OF AFD DAILY LOG PAGES
│   ├── {date folder}               #   The date the scraping was performed
│   │   ├── {date}.txt              #   The date of the AFD daily log
│   │   |                           #   Example URL: https://en.wikipedia.org/wiki/Wikipedia:Articles_for_deletion/Log/2019_August_24
|
├── individual_afd_analysis/        #   FEATURES DERIVED FROM INDIVIDUAL WIKI PAGES NOMINATED FOR DELETION
│   ├── {date folder}               #   The date the scraping was performed
│   │   ├── {Wiki page ID}.txt      #   A unique identifier of the page nominated for deletion
|
├── individual_afd_discussion_page/ #   SCRAPED DAILY SNAPSHOT OF AFD DISCUSSION FOR AN INDIVIDUAL WIKI PAGE
│   ├── {date folder}               #   The date the scraping was performed
│   │   ├── {date}.txt              #   A unique identifier of the page nominated for deletion
|
├── individual_afd_page/            #   METADATA ON INDIVIDUAL WIKI PAGES NOMINATED FOR DELETION
│   ├── {date folder}               #   The date the scraping was performed
│   │   ├── {Wiki page ID}.txt      #   A unique identifier of the page nominated for deletion
|
├── individual_afd_page_html/       #   SCRAPED DAILY SNAPSHOT OF WIKI PAGES NOMINATED FOR DELETION
│   ├── {date folder}               #   The date the scraping was performed
│   │   ├── {Wiki page ID}.txt      #   A unique identifier of the page nominated for deletion
```


## Works Cited
[1] 
Krämer, Katrina. "Female scientists' pages keep disappearing from Wikipedia – what's going on?" Chemistry World. 03 July 2019. <a href="https://www.chemistryworld.com/news/female-scientists-pages-keep-disappearing-from-wikipedia--whats-going-on/3010664.article.">https://www.chemistryworld.com/news/female-scientists-pages-keep-disappearing-from-wikipedia--whats-going-on/3010664.article</a>  
[2] Harrison, Stephen. "How the Sexism of the Past Reinforces Wikipedia's Gender Gap." Slate Magazine. 26 Mar. 2019. <a href="https://slate.com/technology/2019/03/wikipedia-women-history-notability-gender-gap.html">https://slate.com/technology/2019/03/wikipedia-women-history-notability-gender-gap.html.</a>  
[3] Gender equity report 2018. https://meta.wikimedia.org/wiki/Gender_equity_report_2018/Barriers_to_equity.  
[4] Erhard, Ed. "Why didn’t Wikipedia have an article on Donna Strickland, winner of a Nobel Prize?" Wikimedia Foundation. 4 Oct. 2018. <a href="https://wikimediafoundation.org/news/2018/10/04/donna-strickland-wikipedia/">https://wikimediafoundation.org/news/2018/10/04/donna-strickland-wikipedia/</a>  
[5] Bazely, Dawn. "Why Nobel winner Donna Strickland didn’t have a Wikipedia page." Washington Post. 8 Oct. 2018. <a href="https://www.washingtonpost.com/outlook/2018/10/08/why-nobel-winner-donna-strickland-didnt-have-wikipedia-page/">https://www.washingtonpost.com/outlook/2018/10/08/why-nobel-winner-donna-strickland-didnt-have-wikipedia-page/</a>
