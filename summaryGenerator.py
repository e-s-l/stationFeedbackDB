#!/usr/bin/env python

import MySQLdb as mariadb
from astropy.table import vstack, Table, Column
from astropy.time import Time
import numpy as np
import matplotlib.pyplot as plt
import argparse
from reportlab.pdfgen.canvas import Canvas
from datetime import datetime
from adjustText import adjust_text
import textwrap



def parseFunc():
    # Argument parsing
    parser = argparse.ArgumentParser(description="""Current draft script for a report/summary generator that interacts with the SQL database and
                                        extracts data over a requested time range.""")
    parser.add_argument('station',
                        help="""2 letter station code of the station you would like to extract data for.""")
    parser.add_argument('sql_db_name', 
                        help="""The name of the SQL database you would like to use.""")
    parser.add_argument('date_start', 
                        help="""Start date (in MJD) of the time period.""")
    parser.add_argument('date_stop', 
                        help="""The end date (in MJD) of the time period.""")
    parser.add_argument('output_name',
                        help="""File name for output PDF.""")
    parser.add_argument('sql_search', default='%',
                        help="""SQL search string.""")
    args = parser.parse_args()
    return args

def extractStationData(station_code, database_name, mjd_start, mjd_stop, search='%'):
    conn = mariadb.connect(user='auscope', passwd='password')
    cursor = conn.cursor()
    query = "USE " + database_name +";"
    cursor.execute(query)
    query = "SELECT ExpID, Date, Date_MJD, Performance, Performance_UsedVsRecov, W_RMS_del, Detect_Rate_X, Detect_Rate_S, Total_Obs, Notes, Pos_X, Pos_Y, Pos_Z, Pos_E, Pos_N, Pos_U FROM " + station_code+ " WHERE ExpID LIKE \"" + search + "\" AND Date_MJD > " + str(mjd_start) + " AND Date_MJD < " + str(mjd_stop) + " ORDER BY DATE ASC;"
    cursor.execute(query)
    result = cursor.fetchall()
    return result

def wRmsAnalysis(results):
    table = Table(rows=results)
    # filter dummy data
    bad_data = []
    for i in range(0, len(table['col5'])):
        if table['col5'][i] == -999:
            bad_data.append(i)
    table.remove_rows(bad_data)
    time_data = Column(table['col1'], dtype=Time)
    #print("Number of sessions: " + str(len(table['col5'])))
    wrms_med_str = "Median station W.RMS over period: " + str(np.median(table['col5'])) + " ps"
    print(wrms_med_str)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(time_data, table['col5'], color='k', s=20)
    #ax.plot(mjd_x, wrms_runavg, color='r')
    ax.set_xlabel('Date')
    ax.set_ylabel('W.RMS (ps)')
    ax.set_title('Station W.RMS vs. Time')
    ax.grid(axis='y', alpha=0.3, linestyle='--', zorder=0)
    ax.set_xlim([np.min(time_data), np.max(time_data)])
    ax.tick_params(axis='x', labelrotation=90)
    plt.savefig('wRMS.png', bbox_inches="tight")
    return ax, wrms_med_str

def performanceAnalysis(results):
    table = Table(rows=results)
    # filter sessions with 0% data
    bad_data = []
    for i in range(0, len(table['col3'])):
        if table['col3'][i] == 0:
            bad_data.append(i)
    table.remove_rows(bad_data)
    time_data = Column(table['col1'], dtype=Time)
    perf_str = "Median station 'Performance' (used/scheduled) over period: " + str(np.median(table['col3']))
    print(perf_str)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(time_data, table['col3'], color='k', s=10, marker='s')
    ax.fill_between(time_data, table['col3'], alpha = 0.5)
    #ax.plot(mjd_x, wrms_runavg, color='r')
    ax.set_title('Performance (used/scheduled) vs. Time')
    ax.set_xlabel('Date')
    ax.set_ylim([0, 1.0])
    ax.grid(axis='y', alpha=0.3, linestyle='--', zorder=0)
    ax.set_xlim([np.min(time_data), np.max(time_data)])
    ax.tick_params(axis='x', labelrotation=90)
    plt.savefig('performance.png', bbox_inches="tight")
    return ax, perf_str

def posAnalysis(results, coord):
    if coord == 'X':
        col_name = 'col10'
    elif coord == 'Y':
        col_name = 'col11'
    elif coord == 'Z':
        col_name = 'col12'
    elif coord == 'E':
        col_name = 'col13'
    elif coord == 'N':
        col_name = 'col14'
    elif coord == 'U':
        col_name = 'col15'
    table = Table(rows=results)
    # filter sessions with 0% data
    bad_data = []
    for i in range(0, len(table[col_name])):
        if table[col_name][i] == 0:
            bad_data.append(i)
    table.remove_rows(bad_data)
    time_data = Column(table['col1'], dtype=Time)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    lim_offset = np.median(table[col_name])
    ax.scatter(time_data, table[col_name], color='k', s=20)
    #ax.plot(mjd_x, wrms_runavg, color='r')
    ax.set_title(coord + '_pos vs. Time')
    ax.set_xlabel('Date')
    ax.set_ylabel(coord + ' (mm)')
    ax.set_ylim([lim_offset-250, lim_offset+250])
    ax.set_xlim([np.min(time_data), np.max(time_data)])
    ax.grid(axis='y', alpha=0.3, linestyle='--', zorder=0)
    ax.tick_params(axis='x', labelrotation=90)
    plt.savefig(coord + '_pos.png', bbox_inches="tight")
    return ax

def usedVsRecoveredAnalysis(results):
    table = Table(rows=results)
    # filter sessions with 0% data
    bad_data = []
    for i in range(0, len(table['col4'])):
        if table['col4'][i] == 0 or table['col4'][i] == None:
            bad_data.append(i)
    table.remove_rows(bad_data)
    time_data = Column(table['col1'], dtype=Time)
    #print("Number of sessions: " + str(len(table['col4'])))
    #print("Median used vs recovered observations: " + str(np.median(table['col4'])))
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(time_data, table['col4'], color='k', s=5)
    ax.fill_between(time_data, table['col4'], alpha = 0.5)
    ax.set_title('Fractional Used/Recovered Observations vs. Time')
    ax.set_xlabel('MJD (days)')
    ax.set_ylim([0, 1.0])
    ax.set_xlim([np.min(time_data), np.max(time_data)])
    ax.tick_params(axis='x', labelrotation=90)
    return ax

def detectRate(results, band):
    if band == 'X':
        col_name = 'col6'
    elif band == 'S':
        col_name = 'col7'
    table = Table(rows=results)
    # filter sessions with 0% data
    bad_data = []
    for i in range(0, len(table[col_name])):
        if table[col_name][i] == 0 or table[col_name][i] == None:
            bad_data.append(i)
    table.remove_rows(bad_data)
    time_data = Column(table['col1'], dtype=Time)
    rate_str = "Median " + band + "-band detection rate: " + str(np.median(table[col_name]))
    print(rate_str)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(time_data, table[col_name], color='k', s=5)
    ax.fill_between(time_data, table[col_name], alpha = 0.5)
    ax.set_title('Session ' + band + '-band Detection ratio')
    ax.set_ylabel('Fraction of usable obs. vs. correlated obs.')
    ax.set_xlabel('Date')
    ax.set_ylim([0, 1.0])
    ax.set_xlim([np.min(time_data), np.max(time_data)])
    ax.tick_params(axis='x', labelrotation=90)
    # session labels
    #for i, txt in enumerate(table['col0']):
    #    ax.text(time_data[i], table[col_name][i], txt, rotation=90, verticalalignment='top', fontsize=6)
    #txt_height = 0.04*(plt.ylim()[1] - plt.ylim()[0])
    #txt_width = 0.02*(plt.xlim()[1] - plt.xlim()[0])
    #adjust_text(texts, only_move={'points':'y', 'texts':'y'}, arrowprops=dict(arrowstyle="->", color='r', lw=0.5))
    plt.savefig(band + '_detect_rate.png', bbox_inches="tight")
    return ax, rate_str

def problemExtract(results):
    problem_flag = ['pcal', 'phase', 'bad', 'lost', 'clock', 
                    'error', ' late ', 'issue', 'sensitivity',
                    'minus', 'removed']
    table = Table(rows=results)
    bad_data = []
    for i in range(0, len(table['col9'])):
        if table['col9'][i] == '' or table['col9'][i] == None:
            bad_data.append(i)
    table.remove_rows(bad_data)
    problem_list = []
    for j in range(0,len(table['col9'])):
        problem = table['col0'][j].upper() + ': ' + table['col9'][j]
        problem = problem.replace("Applied manual phase calibration", "")
        if any(element in problem.lower() for element in problem_flag): # see if a 'problem' flag is present in the notes
            #if not "manual phase calibration" in problem.lower(): # filter out the generic manual pcal notes
            problem = textwrap.wrap(problem, 160)
            problem_list.append(problem)
    return problem_list

def generatePDF(pdf_name, start, stop, station, str2, str3, str4, str5, problem_string):
    # Page 1
    report = Canvas(pdf_name)
    report.setFont('Helvetica-Bold', 20)
    report.drawString(50, 780, station + ' station report (' + start.iso + ' - ' + stop.iso + ')' )
    t1 = report.beginText()
    t1.setFont('Helvetica-Bold', 10)
    t1.setTextOrigin(50, 750)
    t1.textLines(str2 + str3 + "\n" + str4 + "\n" + str5) 
    report.drawText(t1)
    report.drawInlineImage( 'wRMS.png', 20, 320, width=280, preserveAspectRatio=True)
    report.drawInlineImage( 'performance.png', 300, 320, width=280, preserveAspectRatio=True)
    report.drawInlineImage( 'U_pos.png', 20, 100, width=180, preserveAspectRatio=True)
    report.drawInlineImage( 'E_pos.png', 200, 100, width=180, preserveAspectRatio=True)
    report.drawInlineImage( 'N_pos.png', 380, 100, width=180, preserveAspectRatio=True)
    report.showPage()
    # Page 2
    report.setFont('Helvetica-Bold', 12)
    report.drawString(50, 780, "Reported issues (as extracted from correlation reports)")
    t2 = report.beginText()
    t2.setTextOrigin(50, 750)
    t2.setFont('Helvetica', 5)
    for line in problem_string:
        t2.textLines(line)
    report.drawText(t2)
    report.showPage()
    report.save()

def text_plotter(x_data, y_data, text_positions, axis,txt_width,txt_height):
    for x,y,t in zip(x_data, y_data, text_positions):
        axis.text(x - .03, 1.02*t, '%d'%int(y),rotation=0, color='blue', fontsize=13)
        if y != t:
            axis.arrow(x, t+20,0,y-t, color='blue',alpha=0.2, width=txt_width*0.0,
                        head_width=.02, head_length=txt_height*0.5,
                        zorder=0,length_includes_head=True)

def main(stat_code, db_name, start, stop, output_name, search='%'):
    start_time = Time(start, format='yday', out_subfmt='date')
    stop_time = Time(stop, format='yday', out_subfmt='date')
    result = extractStationData(stat_code, db_name, start_time.mjd, stop_time.mjd, search)
    table = Table(rows=result)
    #time_data = Column(table['col1'], dtype=Time)
    intro_str = stat_code + ' data extracted for time range: ' + start_time.iso + " through " + stop_time.iso
    tot_sess_str = "\nTotal number of " + str(stat_code) + " sessions found in database for this time range: " + str(len(table['col4']))
    tot_obs_str = "\nTotal number of " + str(stat_code) + " observations across all sessions in this time range: " + str(np.nansum(table['col8'].astype(float)).astype(int))
    print(intro_str + tot_sess_str + tot_obs_str)
    ax_two, wrms_str = wRmsAnalysis(result)
    ax_one, perf_str = performanceAnalysis(result)
    #ax_four, detectX_str = detectRate(result, 'X')
    #ax_four, detectS_str = detectRate(result, 'S')
    #ax_five,  = detectRate(result, 'S')
    #ax_six = posAnalysis(result, 'X')
    #ax_seven = posAnalysis(result, 'Y')
    #ax_eight = posAnalysis(result, 'Z')
    ax_nine = posAnalysis(result, 'E')
    ax_ten = posAnalysis(result, 'N')
    ax_eleven = posAnalysis(result, 'U')
    # Make the PDF report
    problems = problemExtract(result)
    print('Generating PDF report...')
    generatePDF(output_name, start_time, stop_time, stat_code, tot_sess_str, tot_obs_str, wrms_str, perf_str, problems)
    #plt.show()
    return
    
if __name__ == '__main__':
    args = parseFunc()
    main(args.station, args.sql_db_name, args.date_start, args.date_stop, args.output_name, args.sql_search)
