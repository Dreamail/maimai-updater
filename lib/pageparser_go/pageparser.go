package pageparser

import (
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
	"strconv"
	"strings"

	"github.com/antchfx/htmlquery"
)

type Record struct {
	Achievements float64 `json:"achievements"`
	DxScore      int     `json:"dxScore"`
	LevelIndex   int     `json:"level_index"`
	Title        string  `json:"title"`
	Type         string  `json:"type"`
	FC           string  `json:"fc"`
	FS           string  `json:"fs"`
}

var (
	diffStr = []string{"basic", "advanced", "expert", "master", "remaster"}
)

func ParseRecords(achievementsvs, dxscorevs string, diff int) (string, error) {
	recordMap := make(map[string]*Record, 0)
	parseFunc := func(body string) error {
		doc, err := htmlquery.Parse(strings.NewReader(body))
		if err != nil {
			return err
		}
		elements := htmlquery.Find(doc, fmt.Sprintf(`//div[@class="music_%s_score_back w_450 m_15 p_3 f_0"]`, diffStr[diff]))
		if len(elements) == 0 {
			return errors.New("record was not found")
		}

		link_searched := false // fuck duplicated name
		for _, e := range elements {
			scoreString := strings.TrimSpace(htmlquery.InnerText(htmlquery.Find(e, fmt.Sprintf(`//table[@class="f_14 t_c"]/tbody/tr/td[@class="p_r %s_score_label w_120 f_b"]`, diffStr[diff]))[1]))
			if scoreString == "― %" || scoreString == "―" {
				continue
			}

			title := htmlquery.InnerText(htmlquery.FindOne(e, `//div[@class="music_name_block t_l f_13 break"]`))

			if title == "Link" && !link_searched { // the frist Link shoud be niconico & VOCALOID grene
				title = "Link(CoF)"
				link_searched = true
			}

			kindIconSrc := htmlquery.SelectAttr(htmlquery.FindOne(e, `//img[@class="music_kind_icon f_r"]`), "src")
			kind := "DX"
			if strings.Contains(kindIconSrc, "standard") {
				kind = "SD"
			}

			if record, ok := recordMap[title+kind]; ok {
				if strings.Contains(scoreString, "%") {
					achievements, err := strconv.ParseFloat(strings.ReplaceAll(scoreString, "%", ""), 64) // who will add a whitespace between number and % ?
					if err != nil {
						return err
					}
					record.Achievements = achievements
				} else {
					dxScore, err := strconv.ParseInt(strings.ReplaceAll(scoreString, ",", ""), 10, 32)
					if err != nil {
						return err
					}
					record.DxScore = int(dxScore)
				}
				continue
			}
			recordMap[title+kind] = &Record{
				Title: title,
			}
			if strings.Contains(scoreString, "%") {
				achievements, err := strconv.ParseFloat(strings.ReplaceAll(scoreString, "%", ""), 64)
				if err != nil {
					return err
				}
				recordMap[title+kind].Achievements = achievements
			} else {
				dxScore, err := strconv.ParseInt(strings.ReplaceAll(scoreString, ",", ""), 10, 32)
				if err != nil {
					return err
				}
				recordMap[title+kind].DxScore = int(dxScore)
			}

			recordMap[title+kind].Type = kind

			iconEles := htmlquery.Find(e, `//table[@class="f_14 t_c"]/tbody/tr/td/img[@class="h_30 f_r"]`)
			for _, ie := range iconEles {
				icon := regexp.MustCompile(`music_icon_(.*?).png`).FindStringSubmatch(htmlquery.SelectAttr(ie, "src"))
				if strings.Contains(icon[1], "fc") || strings.Contains(icon[1], "ap") {
					switch icon[1] {
					case "fc":
						recordMap[title+kind].FC = "fc"
					case "fcp":
						recordMap[title+kind].FC = "fcp"
					case "ap":
						recordMap[title+kind].FC = "ap"
					case "app":
						recordMap[title+kind].FC = "app"
					}
				}
				if strings.Contains(icon[1], "fs") {
					switch icon[1] {
					case "fs":
						recordMap[title+kind].FS = "fs"
					case "fsp":
						recordMap[title+kind].FS = "fsp"
					case "fsd":
						recordMap[title+kind].FS = "fsd"
					case "fsdp":
						recordMap[title+kind].FS = "fsdp"
					}
				}
				if recordMap[title+kind].FC != "" && recordMap[title+kind].FS != "" {
					break
				}
			}

			recordMap[title+kind].LevelIndex = diff
		}
		return nil
	}
	err := parseFunc(dxscorevs)
	if err != nil {
		return "", err
	}
	err = parseFunc(achievementsvs)
	if err != nil {
		return "", err
	}

	records := make([]Record, 0)
	for _, r := range recordMap {
		records = append(records, *r)
	}

	byrec, err := json.Marshal(records)
	if err != nil {
		return "", err
	}
	return string(byrec), nil
}
