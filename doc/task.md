重命名 appointmentchecker 里的函数名。
区分概念呢，一共是有 6 个页面，也就是6 个 schritt_x_page，在每个页面上有对应的 action。

改成 enter_schritt_x_page.
然后每一个 enter_schritt_x_page 里都要包含进入到相应的页面后的操作逻辑。

比如 schritt4 页面就要检查 appointment 是否可用。
schritt5 页面就要提交表单信息。

把 schritt4 的 select_appointment_and_choose_profile，提出到新的 python 文件中。