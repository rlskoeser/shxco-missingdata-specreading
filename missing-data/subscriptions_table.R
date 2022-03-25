# name required packages
list.of.packages <- c("ggplot2", "glue", "gt", "tidyverse", "webshot", "paletteer", "gtExtras")

# install required packages, if necessary, and load them ----
{
  new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
  if(length(new.packages)) install.packages(new.packages)
  lapply(list.of.packages, require, character.only = TRUE)
}

iris
subscriptions_df <- read_csv('subscriptions_data.csv')

View(subscriptions_df)

plot_chart <- function(data){
  data %>% 
    ggplot(aes(x=year, y=counts)) + 
    geom_bar(stat="identity") +
    theme_void() +
    theme(legend.position = "none")
}

sub_plots <- subscriptions_df %>% group_by(event_type, .drop=FALSE) %>% 
  summarise(sum_counts = sum(counts), year = year, counts = counts) %>%
  arrange(desc(sum_counts)) %>% select(-sum_counts) %>% 
  nest(subs = c(year, counts)) %>% mutate(plot = map(subs, plot_chart))


subs_table <- subscriptions_df %>% 
  group_by(event_type) %>%
  summarise(counts = sum(counts)) %>%
  arrange(desc(counts)) %>%
  mutate(ggplot = NA) %>% 
  gt() %>% 
  text_transform(
    locations = cells_body(vars(ggplot)),
    fn = function(x){
      map(sub_plots$plot, ggplot_image, height = px(25), aspect_ratio = 5)
    }
  ) %>% 
  cols_label(
    ggplot = md("Event Frequency \nfrom 1919-1942"),
    event_type = "Event Type",
    counts = "Number of Events"
  )  %>% cols_align(align = "center", columns = everything()) %>% tab_header(
    title = md('Types of Membership Activity'),
    subtitle = md('Separated by event category and summarizing overall activity.')
  )%>%opt_table_font(
    font = list(
      google_font(name = "Garamond"),
      "Cochin", "Serif"
    ),
    weight= 'normal'
  ) %>%
  tab_footnote(
    footnote = "Frequency not scaled across event types.",
    locations = cells_column_labels(
      columns = c(ggplot)
    )
  )

subs_table

subs_table %>%
  gtsave(
    glue::glue("subs_table.png")
    # path = tempdir()
  )






