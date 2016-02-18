'''
Generates the CSV datafiles for the resistors drwares front labels 
'''
import csv

series = [[1, 1.2, 1.5], [1.8, 2.2, 2.7], [3.3, 3.9, 4.7], [5.6, 6.8, 8.2],
          [10, 12, 15], [18, 22, 27], [33, 39, 47], [56, 68, 82],
          [100, 120, 150], [180, 220, 270], [330, 390, 470], [560, 680, 820]]

suffixes = ['', 'k', 'M']

rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
cols = ['1', '2', '3', '4', '5', '6']

if __name__ == '__main__':
  with open('resistors3x_data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(['val1', 'val2', 'val3', 'gridid'])
    
    row_ind = 0
    col_ind = 0
    
    for suffix in suffixes:
      for vals in series:
        writer.writerow(['%s%s' % (vals[0], suffix),
                         '%s%s' % (vals[1], suffix),
                         '%s%s' % (vals[2], suffix),
                         '%s-%s' % (rows[row_ind], cols[col_ind])])
        row_ind += 1
        if row_ind >= len(rows):
          row_ind = 0
          col_ind += 1
        assert col_ind < len(cols)