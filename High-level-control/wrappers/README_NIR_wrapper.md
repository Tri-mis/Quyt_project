# Đây là cách sử dụng thư viện NIR
Thư viện này viết theo dạng hướng đối tượng, nghĩa là một đối tượng lập trình sẽ được dùng để đại diện cho máy đo NIRScan Nano (gọi tắt là NIR)
- Đầu tiên thì kết nối NIR với máy tính thông qua cổng USB
- Để dùng được thì đầu tiên ta tạo một đối tượng NIR sử dụng class NIR_SPECTROMETER()
    nir = NIR_SPECTROMETER()
- Giờ thì nir là cái đối tượng lập trình đại diện cho con cảm biến NIR nhá, thấy chỗ nào ghi nir nghĩa là đang nhắc tới cái đối tượng lập trình, còn chỗ nào ghi NIR thì nghĩa là đang nhắc tới cái con cảm biến NIR.
- Rồi giờ thì để con NIR scan được thì mình sẽ phải cài đặt thông số scan cho nó thông qua biến scan_config của đối tượng nir. Trong biến scan_config nó có các biến nhỏ khác, cụ thể:
    - scan_config.scan_type: biến này để đặt kiểu scan cho con NIR, cái này phức tạp, từ từ giải thích sau
    - scan_config.scanConfigIndex: đây là cái số thứ tự mà cái scan_config này sẽ được lưu trong con NIR. cái này k quan trọng lắm
    - scan_config.ScanConfig_serial_number: đây cũng là một dạng chuỗi ký tự để đặt tên có cái thiết lập scan_config này thôi, không quan trọng lắm
    - scan_config.config_name: tương tự, k quan trọng
    - scan_config.wavelength_start_nm: đây là giới hạn bước sóng đầu tiên được lấy dữ liệu. Cái này quan trọng, vì nó sẽ cài đặt cái khoảng bước sóng để lấy dữ liệu của lần scan, tuy nhiên không cần đổi thông số cái này cứ đặt nó là = 900 nm là được
    - scan_config.wavelength_end_nm: này là giới hạn bước sóng cuối cùng được lấy dữ liệu. cái này tương tự cái trên, cứ đặt nó là 1700 là được
    *** wavelength_start_nm và wavelength_end_nm chỉ đặt ra giới hạn thôi, bước sóng được lấy dữ liệu sẽ nằm trong khoảng 900 - 1700 nm chứ không nhất thiết nó phải lấy ngay bước sóng 900 hay 1700 nm nha. Cụ thể các bước sóng nào được lấy dữ liệu thì còn phụ thuộc vô một số biến khác và tính toán của bộ xử lý bên trong con NIR nữa.
    - scan_config.width_px: có thể hiểu đây là cài đặt khoảng các giữa hai bước sóng liên tiếp được scan, nói cách khác nó là độ phân giải của dãy bước sóng. Biến này càng nhỏ thì độ phân giải càng lớn => dữ liệu chính xác hơn, nhưng cũng nhiều hơn => xử lý lâu hơn. Thường thì biến này được đặt khoảng 6 - 7 px. Biến này quan trọng vì nó sẽ góp phần xác định bước sóng nào được sử dụng
    - scan_config.num_patterns: Đây là số lượng bước sóng được scan, biến này cũng quan trọng vì nó sẽ góp phần xác định bước sóng nào được sử dụng
    - scan_config.num_repeats: Biến này xác định số lần scan trên một điểm. Nghĩa là vầy, thực ra khi con NIR scan thì nó không chỉ đọc dữ liệu 1 lần, mình có thể cài cho nó đọc dữ liệu nhiều lần (thông qua biến num_repeats này), đọc liên tục, xong trả ra kết quả cuối cùng sẽ là trung bình cộng của các lần đọc đó. Việc này là để dữ liệu mượt hơn, và loại bớt đi tín hiệu nhiễu.

    - Nói tóm lại, các điểm quang trọng nhất của cài đặt cho con NIR scan sẽ là:
        - scan_type
        - wavelength_start_nm
        - wavelength_end_nm
        - width_px
        - num_patterns
        - num_repeats
    