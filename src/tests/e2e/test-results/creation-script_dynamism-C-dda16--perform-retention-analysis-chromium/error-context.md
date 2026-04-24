# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - alert [ref=e2]
  - generic [ref=e3]:
    - generic [ref=e5]:
      - generic [ref=e6]:
        - img [ref=e8]
        - heading "ALPHAHECTA" [level=1] [ref=e10]
        - paragraph [ref=e11]: Log in to your high-velocity workflow
      - generic [ref=e12]:
        - generic [ref=e13]:
          - text: Username
          - generic [ref=e14]:
            - img [ref=e15]
            - textbox "Username" [ref=e18]:
              - /placeholder: commander
        - generic [ref=e19]:
          - text: Password
          - generic [ref=e20]:
            - img [ref=e21]
            - textbox "Password" [ref=e24]:
              - /placeholder: ••••••••
        - generic [ref=e26] [cursor=pointer]:
          - checkbox "Remember me" [ref=e27]
          - generic [ref=e28]: Remember me
        - button "AUTHENTICATE" [ref=e29]:
          - text: AUTHENTICATE
          - img [ref=e30]
      - paragraph [ref=e32]:
        - text: New to Ettametta?
        - link "Register Access" [ref=e33] [cursor=pointer]:
          - /url: /register
    - region "Notifications alt+T"
```