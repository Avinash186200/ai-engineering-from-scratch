// Excel: Data > Get Data > From Other Sources > Blank Query > Advanced Editor, paste this.
// Then Close & Load. Refresh (Data > Refresh All) pulls the latest ranking from the same model the AI assistant uses.
//
// Setup:
//   1. Put the ranking date in a cell, select it, Formulas > Define Name: AsOf   (e.g. 2025-06-19)
//   2. Put your API key in Data source settings or a named cell ApiKey kept out of shared copies.
//      Never paste a key into a workbook you email around.
//   3. Privacy level: Organizational. When asked, connect Anonymously (the key goes in the header below).
let
    BaseUrl = "https://models.example.com",
    AsOf    = Text.From(Excel.CurrentWorkbook(){[Name="AsOf"]}[Content]{0}[Column1]),
    ApiKey  = Text.From(Excel.CurrentWorkbook(){[Name="ApiKey"]}[Content]{0}[Column1]),

    Response = Json.Document(
        Web.Contents(BaseUrl, [
            RelativePath = "v2/rank",
            Query        = [as_of = AsOf, top_n = "10"],
            Headers      = [#"X-API-Key" = ApiKey],
            Timeout      = #duration(0, 0, 0, 60)
        ])),

    Top      = Response[top],
    AsTable  = Table.FromRecords(Top),
    Typed    = Table.TransformColumnTypes(AsTable, {
                   {"rank", Int64.Type}, {"fund", type text},
                   {"predicted_return_pct", type number}, {"nav", type number}}),
    WithMeta = Table.AddColumn(
                   Table.AddColumn(Typed, "as_of_used", each Response[as_of_used], type text),
                   "model_version", each Response[model_version], type text)
in
    WithMeta

// Why RelativePath + Query instead of building the URL by hand:
//   Power Query treats the base URL as the data source for credentials and privacy, and refresh in the
//   Power BI service works only when the base URL is static. Show model_version and as_of_used in the sheet
//   so whoever reads it knows exactly what produced the numbers.
