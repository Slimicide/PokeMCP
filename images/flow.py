# Rendered in Windows Terminal - Misalignment in art corrects misalignment during rendering

flow = r"""		                                                             
                                                                                     ⢠⠞⠉⠉⢳
                                                                                     ⢸⡀⠀⠀⣠⡇
                                                                                      ⠙⡖⢾⠋
                                                                                      ⢸⠁⠸⡄
                                                                                      ⡞⠀⠀⣇
                                                                            ⢰⠒⠒⠒⠒⠒⠒⠲⠲⠚⠓⠒⠒⠛⠓⢒⣖⠒⠒⠒⠒⠒⠒⢲
                                                                            ⣼⠀⠀⠀⠀   ⢠⠖⠋⠉⠷⣄⠀⠀⢠⠖⠉⠉⠑⢦ ⢸
                                                                            ⡟⠉⢻⠀⠀⠀⠀ ⣿⣾⣿⣦⡀⢸⠀⠀⢿⣿⣿⣷⡀⢸⠀⢸⠋⠙⡇
                                                                            ⡇⠀⢸⠀⠀⠀  ⠘⢿⣿⢟⣂⠞⠀⠀⠈⠿⣿⣿⣡⠞⠀⢸⠀⠀⡇
                                                                            ⡇⣾⠉⠉⠙⢧⡀⠀              ⣠⠞⠉⠉⡙
                                                                            ⠉⣻⠀⠀⠀⠀⠙⢦⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣠⠞⠁⠀⠀ ⠀⡏
                                                                             ⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀    ⡇
                                                                             ⠿⡤⣤⣤⣤⣤⣤⣤⣤⣤⣤⢤⠤⠤⠤⠤⢤⣤⣤⣤⣤⣤⣤⡤⢤⣤⠇
                                                                                 |                |
                                                                 6              /|\              \|/            1
                                                          Updated gamestate      |                |         mGBA input
                                                            (Screenshots)        |                |         (Controls)
                                                       (Dialogue transcripts)    |                |    (Screenshot requests)
                                                                                /|\              \|/
                                                                                 |                |
                                                                            ----------------------------
                                                                            |                          |
                                                                   ---------|         PokeMCP          |O]
                                                                   |        |                          |  `.
                                                                   |        ----------------------------    \ 
                                                                   |                     |                   |
                                                                   |                    /|\                 .`
                                                                   |             5       |        5         |
                                                                  \|/     Upscale images | Extract dialogue  `._ 
                                                                   |        Apply grid   |                      :
                                                                   |                    /|\                     |
                                                                   |                     |                     /
                                                                   |        ----------------------------      /
                                                        3          |        |                          |      ;
                                                 Monitor for fresh |        |     Image Processing     |     .`                |
                                                    screenshots    |        |           OCR            |     |                \|/
                                                                   |        |                          |     `.                |     1
                                                                   |        ----------------------------       ;               | mGBA input
                                                                   |                     |                      `..            |
                                                                   |                    /|\                        `._        \|/
                                                                   |            4        |                            `.       |
                                                                  \|/     New screenshot |                              |
                                                                   |         detected    |                             .` 
                                                                   |                    /|\                           .`
                                                                   |                     |                           .`
                                                                   |        -----------------------------            ;
                                                                   |        |                           |          .`
                                                                   ---------|        gamestate/         |         ;
                                                                            |                           |         :
                                                                            -----------------------------          `.
                                                                                         |                           `.
                                                                                        /|\                            `.
                                                                                 2       |                              |
                                                                         Save screenshot |                               `._
                                                                                         |                                  `.
                                                                                        /|\                                  `.__
                                                                                         |                   1                |O|
                                                                            -----------------------------  mGBA   ----------------------------
                                                                            |                           |  input  |                          |
                                                                            |           mGBA            |--<---<--|      mGBA Scripting      |
                                                                            |                           |         |                          |
                                                                            -----------------------------         ----------------------------
                                                                              |    Pokemon Emerald    |             |    mGBA_server.lua   |
                                                                              -------------------------             ------------------------
"""
print(flow)